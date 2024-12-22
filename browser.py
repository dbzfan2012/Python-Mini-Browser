import tkinter
import tkinter.font

from url import *
from parameters import *

from htmlparser import *

from cssparser import *

import urllib
import urllib.parse

from jscript import *

#import layout1
from layout import *

browser6_styles = open("browser6.css")
DEFAULT_STYLE_SHEET = CSSParser(browser6_styles.read()).parse()
    
def tree_to_list(tree, list):
    list.append(tree)
    for child in tree.children:
        tree_to_list(child, list)
    return list

class Browser:
    def __init__(self):        
        self.window = tkinter.Tk()
        self.canvas = tkinter.Canvas(
            self.window,
            width=WIDTH,
            height=HEIGHT,
            bg="white",
        )
        self.canvas.pack()

        self.window.bind("<Down>", self.handle_down)
        self.window.bind("<Up>", self.handle_up)
        self.window.bind("<Button-1>", self.handle_click)
        self.window.bind("<Key>", self.handle_key)
        self.window.bind("<BackSpace>", self.handle_backspace)
        self.window.bind("<Return>", self.handle_enter)
        self.window.bind("<Button-2>", self.handle_middle_click)
        self.window.bind("<Control-v>", self.handle_paste)
        self.window.bind("<Tab>", self.handle_tab)
        
        self.focus = None

        self.tabs = []
        self.active_tab = None
        self.chrome = Chrome(self)
        
        self.bookmarks = []
        
    def handle_down(self, e):
        self.active_tab.scrolldown()
        self.draw()
        
    def handle_paste(self, e):
        # get clipboard text
        self.chrome.address_bar = self.window.clipboard_get()
        self.draw()
        
    def handle_tab(self, e):
        if self.active_tab:
            self.active_tab.handle_tab()
        
    def handle_middle_click(self, e):
        if e.y < self.chrome.bottom:
            return
        else:
            tab_y = e.y - self.chrome.bottom
            new_url = self.active_tab.middle_click(e.x, tab_y)
            self.new_tab_not_active(new_url)
        self.draw()

    def handle_click(self, e):
        if e.y < self.chrome.bottom:
            self.focus = None
            self.chrome.click(e.x, e.y)
        else:
            self.focus = "content"
            self.chrome.blur() #browser is no longer focus
            tab_y = e.y - self.chrome.bottom
            self.active_tab.click(e.x, tab_y)
        self.draw()

    def handle_key(self, e):
        if len(e.char) == 0: return
        if not (0x20 <= ord(e.char) < 0x7f): return
        self.chrome.keypress(e.char)
        if self.chrome.keypress(e.char):
            self.draw()
        elif self.focus == "content":
            self.active_tab.keypress(e.char)
            self.draw()
        #self.draw()
        
    def handle_backspace(self, e):
        self.chrome.backspace()
        self.draw()

    def handle_enter(self, e):
        if self.focus == "address_bar":
            self.chrome.enter()
        elif self.focus == "content":
            self.active_tab.handle_enter_while_in_form()
        self.draw()

    def new_tab(self, url):
        new_tab = Tab(height() - self.chrome.bottom, self.bookmarks)
        new_tab.load(url)
        self.active_tab = new_tab
        self.tabs.append(new_tab)
        self.draw()
        
    def new_tab_not_active(self, url):
        new_tab = Tab(height() - self.chrome.bottom, self.bookmarks)
        new_tab.load(url)
        self.tabs.append(new_tab)
        self.draw()

    def draw(self):
        self.canvas.delete("all")
        self.active_tab.draw(self.canvas, self.chrome.bottom)
        for cmd in self.chrome.paint():
            cmd.execute(0, self.canvas)
        
    def handle_up(self, e):
        self.active_tab.scrollup()
        self.draw()
    
class Tab:
    def __init__(self, tab_height, bookmarks):
        self.url = None
        self.focus = None
        #self.window = tkinter.Tk()
        self.history = []
        self.tab_height = tab_height
        self.bookmarks = bookmarks
        
        self.locked = False
        self.refer_policy = None
        # self.canvas = tkinter.Canvas(
        #     self.window,
        #     width = getWidth(),
        #     height = height(),
        #     bg = "white"
        #     )
        # self.canvas.pack(expand = True, fill = "both")       
        
        # self.scroll = 0  #value of scroll at the beginning, increases when user scrolls down
        # self.window.bind("<Down>", self.scrolldown) #down arrow key input
        # self.window.bind("<Up>", self.scroll_up)
        # self.window.bind("<Configure>", self.resize)
        # self.window.bind("<Button-1>", self.click)
    def __repr__(self):
        return "Tab(history={})".format(self.history)
        
    def resize(self, e): 
        setHeight(e.height)
        setWidth(e.width)
        #self.display_list = Layout(self.nodes).display_list
        self.document = DocumentLayout(self.nodes)
        self.document.layout()
        self.display_list = []
        paint_tree(self.document, self.display_list)
        self.draw()
        pass
        
    def scrolldown(self): #"e" is the event, see documentation
        # page_height = self.display_list[len(self.display_list) - 1][1] - height()
        # if (self.scroll <= page_height): #prevents scrolling beyond page height
        #     self.scroll += scroll_step()
        # self.draw()
        max_y = max(self.document.height + 2*vstep() - self.tab_height, 0)
        self.scroll = min(self.scroll + scroll_step(), max_y)
        #self.draw()
        
    def scrollup(self): #"e" is the event, see documentation
        #selfscroll = max(self.scroll - scroll_step(), 0)
        # if (self.scroll > 0): #prevents scrolling above top of page
        #     self.scroll -= scroll_step()
        # self.draw()
        min_y = min(self.document.height + 2*vstep() - self.tab_height, 0)
        self.scroll = max(self.scroll - scroll_step(), min_y)
        
    def keypress(self, char):
        if self.focus:
            if self.js.dispatch_event("keydown", self.focus): return
            self.focus.attributes["value"] += char
            self.render()
            
    def handle_enter_while_in_form(self):
        if not self.focus:
            return
        elt = self.focus
        while elt:
            if elt.tag == "form" and "action" in elt.attributes:
                return self.submit_form(elt)
            elt = elt.parent                
            
    def handle_tab(self):
        objs = [obj for obj in tree_to_list(self.document, [])
                if isinstance(obj, InputLayout)]
        
        if not objs: return
        
        getNext = False
        beginning = objs[0].node
        for obj in objs:
            elt = obj.node
            if getNext:
                elt.attributes["value"] = ""
                self.focus = elt
                break
            if (self.focus == elt):
                getNext = True
                
        if self.focus.tag == "button":
            self.focus = beginning
        
        return self.render()
            
        
    def click(self, win_x, win_y):
        self.focus = None
        page_x, page_y = win_x, win_y + self.scroll
        
        objs = [obj for obj in tree_to_list(self.document, []) 
                if obj.x <= page_x < obj.x + obj.width 
                and obj.y <= page_y < obj.y + obj.height]
        
        if not objs: return
        elt = objs[-1].node
        
        while elt:
            if isinstance(elt, Text):
                #elt = elt.parent
                pass
            elif elt.tag == "a" and "href" in elt.attributes:
                if self.js.dispatch_event("click", elt): return
                url = self.url.resolve(elt.attributes["href"])
                return self.load(url)
            elif elt.tag == "input":
                if self.js.dispatch_event("click", elt): return
                elt.attributes["value"] = ""
                if self.focus:
                    self.focus.is_focused = False
                self.focus = elt
                elt.is_focused = True
                if elt.attributes.get("type", "text") == "checkbox":
                    if 'checked' in elt.attributes:
                        del self.node.attributes["checked"]
                    else:
                        elt.attributes["checked"] = ""
                return self.render()
            elif elt.tag == "button":
                if self.js.dispatch_event("click", elt): return
                while elt:
                    if elt.tag == "form" and "action" in elt.attributes:
                        return self.submit_form(elt)
                    elt = elt.parent
            elt = elt.parent
            
    def submit_form(self, elt):
        if self.js.dispatch_event("submit", elt): return
        inputs = [node for node in tree_to_list(elt, [])
                  if isinstance(node, Element)
                  and node.tag == "input"
                  and "name" in node.attributes]

        body = ""
        for input in inputs:
            name = input.attributes["name"]
            value = input.attributes.get("value", "")
            name = urllib.parse.quote(name)
            
            # if 'checked' not in input.attributes:
            #     #value = "on"
            #     body += name + "=" + value
            # else:
            value = urllib.parse.quote(value)
            if 'checked' in input.attributes and value == '':
                value = 'on'
            if name != '' and value != '':
                body += "&" + name + "=" + value
        body = body[1:]
                
        if "method" in elt.attributes and \
        elt.attributes["method"] == "POST":
            url = self.url.resolve(elt.attributes["action"])
            self.load(url, body)
        elif "method" in elt.attributes and \
        elt.attributes["method"] == "GET":
            url = self.url.resolve(elt.attributes["action"])
            url.appendGet(body, True)
            self.load(url, body)
        else:
            url = self.url.resolve(elt.attributes["action"])
            url.appendGet(body, True)
            self.load(url, body)
            
    def middle_click(self, win_x, win_y):    
        page_x, page_y = win_x, win_y + self.scroll
        
        objs = [obj for obj in tree_to_list(self.document, []) 
                if obj.x <= page_x < obj.x + obj.width 
                and obj.y <= page_y < obj.y + obj.height]
        
        if not objs: return
        elt = objs[-1].node
        
        while elt:
            if isinstance(elt, Text):
                pass
            elif elt.tag == "a" and "href" in elt.attributes:
                url = self.url.resolve(elt.attributes["href"])
                return url
            elt = elt.parent
            
    def go_back(self):
        if len(self.history) > 1:
            self.history.pop()
            back = self.history.pop()
            self.load(back)
            
    def allowed_request(self, url):
        return self.allowed_origins == None or \
            url.origin() in self.allowed_origins
        
    def load(self, url, payload=None):  
        self.scroll = 0
        self.url = url
        self.history.append(url)
        headers, body = url.request(self.url, self.refer_policy, payload)
        if len(headers) > 0 and "https" in str(self.url):
            self.locked = True
        
        self.allowed_origins = None
        if "content-security-policy" in headers:
            csp = headers["content-security-policy"].split()
            if len(csp) > 0 and csp[0] == "default-src":
                self.allowed_origins = []
                for origin in csp[1:]:
                    self.allowed_origins.append(URL(origin).origin())
                    
        if "referrer-policy" in headers:
            self.refer_policy = headers["referrer-policy"]
            
        self.nodes = HTMLParser(body).parse()

        scripts = [node.attributes["src"]
                 for node in tree_to_list(self.nodes, [])
                 if isinstance(node, Element)
                 and node.tag == "script"
                 and "src" in node.attributes]
                
        self.js = JSContext(self)
        for script in scripts:
            script_url = url.resolve(script)
            if not self.allowed_request(script_url):
                print("Blocked script", script, "due to CSP")
                continue     
            try:
                header, body = script_url.request(url, self.refer_policy)
            except:
                continue
            try:
                self.js.run(body)
            except dukpy.JSRuntimeError as e:
                print("Script", script, "crashed", e)
                
        self.rules = DEFAULT_STYLE_SHEET.copy()
        links = [node.attributes["href"]
                 for node in tree_to_list(self.nodes, [])
                 if isinstance(node, Element)
                 and node.tag == "link"
                 and node.attributes.get("rel") == "stylesheet"
                 and "href" in node.attributes]
        for link in links:
            style_url = url.resolve(link)
            if not self.allowed_request(style_url):
                print("Blocked style", link, "due to CSP")
                continue
            try:
                header, body = style_url.request(url, self.refer_policy)
            except:
                continue
            self.rules.extend(CSSParser(body).parse())
            
        id_nodes = [node
               for node in tree_to_list(self.nodes, [])
               if isinstance(node, Element)
               and node.attributes.get("id")]
                    
        self.js.idsToVars(id_nodes)
        
        self.render()
            
    def render(self):
        style(self.nodes, sorted(self.rules, key=cascade_priority))
        self.document = DocumentLayout(self.nodes)
        self.document.layout()
        self.display_list = []
        paint_tree(self.document, self.display_list)
        
    def draw(self, canvas, offset):                   
        for cmd in self.display_list:
            if cmd.rect.top > self.scroll + self.tab_height:
                continue
            if cmd.rect.bottom < self.scroll: continue
            cmd.execute(self.scroll - offset, canvas)
        
        # for page_x, page_y, word, font in self.display_list:
        #     screen_x = page_x            
        #     screen_y = page_y - self.scroll        
            
        #     if screen_y > height(): continue#layout.HEIGHT: continue
        #     if screen_y + vstep() < 0: continue#layout.VSTEP < 0: continue
            
        #     if font == '\N{Grinning Face}':
        #         self.handle_emoji(screen_x, screen_y)
        #         continue
            
        #     self.canvas.create_text(screen_x, screen_y, text=word, font=font, anchor="nw")
            
        # if len(self.display_list) * vstep() > height(): #layout.VSTEP > layout.HEIGHT: # #
        #     self.draw_scroll_bar()
            
    def draw_scroll_bar(self):
        #gets height for page so last characters is at bottom of page
        page_height = self.display_list[len(self.display_list) - 1][1] - height() 
        #gets the total num of scrolls possible to reach the bottom
        num_scrolls = page_height / scroll_step() 
        #gets the increments required for the scrollbar from user POV
        vertical_increment = (self.scroll / scroll_step()) * (height() / 2 / num_scrolls)  
    
        x1 = getWidth() - 8 #width() - 8
        y1 = vertical_increment
        x2 = getWidth() #width()
        y2 = (height() / 2) + vertical_increment
        fill = "blue"
        width = 0

        #Draws the scroll bar
        self.canvas.create_rectangle(x1, y1, x2, y2, fill=fill, width=width)
            
    def handle_emoji(self, screen_x, screen_y):
        emo = tkinter.PhotoImage(file="openmoji/1F600.png")
        emojiglobal.add(emo)
        self.canvas.create_image(screen_x, screen_y, emo)    
        
class Chrome:
    def __init__(self, browser):
        self.browser = browser
        self.focus = None
        self.address_bar = ""
        
        self.font = get_font(20, "normal", "roman", "Times")
        self.font_height = self.font.metrics("linespace")
        
        self.padding = 5
        self.tabbar_top = 0
        self.tabbar_bottom = self.font_height + 2 * self.padding
        
        plus_width = self.font.measure("+") + 2 * self.padding
        self.newtab_rect = Rect(
            self.padding, self.padding,
            self.padding + plus_width, 
            self.padding + self.font_height)
        
        self.urlbar_top = self.tabbar_bottom
        self.urlbar_bottom = self.urlbar_top + \
            self.font_height + 2*self.padding
            
        back_width = self.font.measure("<") + 2 * self.padding
        self.back_rect = Rect(
            self.padding,
            self.urlbar_top + self.padding,
            self.padding + back_width,
            self.urlbar_bottom - self.padding)
        
        self.address_rect = Rect(
            self.back_rect.top + self.padding,
            self.urlbar_top + self.padding,
            getWidth() - self.padding - 25,
            self.urlbar_bottom - self.padding)
        
        self.bookmarks_rect = Rect(
            self.address_rect.right + self.padding,
            self.urlbar_top + self.padding,
            getWidth() - self.padding,
            self.urlbar_bottom - self.padding
        )
        
        self.bottom = self.urlbar_bottom
        
    def blur(self):
        self.focus = None
        
    def click(self, x, y):
        self.focus = None
        if self.newtab_rect.containsPoint(x, y):
            self.browser.new_tab(URL("https://browser.engineering/"))
        elif self.back_rect.containsPoint(x, y):
            self.browser.active_tab.go_back()
        elif self.bookmarks_rect.containsPoint(x, y):
            if str(self.browser.active_tab.url) in self.browser.bookmarks:
                self.browser.bookmarks.remove(str(self.browser.active_tab.url))
            else:
                self.browser.bookmarks.append(str(self.browser.active_tab.url))
        elif self.address_rect.containsPoint(x, y):
            self.focus = "address bar"
            self.address_bar = ""
        else:
            for i, tab in enumerate(self.browser.tabs):
                if self.tab_rect(i).containsPoint(x, y):
                    self.browser.active_tab = tab
                    break
            
    def keypress(self, char):
        self.focus = None
        if self.focus == "address bar":
            self.address_bar += char
            return True
        return False
    
    def handle_enter(self, e):
        if self.focus == "address-bar":
            self.chrome.enter()
        elif self.focus == "content":
            self.active_tab.handle_enter_while_in_form()
        self.draw()
            
    def backspace(self):
        bar_len = len(self.address_bar)
        if self.focus == "address bar" and bar_len > 0:
            self.address_bar = self.address_bar[0:bar_len - 1]
            
    def enter(self):
        if self.focus == "address bar":
            self.browser.active_tab.load(URL(self.address_bar))
            self.focus = None
        
    def tab_rect(self, i):
        tabs_start = self.newtab_rect.right + self.padding
        tab_width = self.font.measure("Tab X") + 2 * self.padding  
        return Rect(
            tabs_start + tab_width * i, self.tabbar_top,
            tabs_start + tab_width * (i + 1), self.tabbar_bottom)
        
    def paint(self):
        cmds = []
        
        cmds.append(DrawRect(
            Rect(0, 0, getWidth(), self.bottom), "white", 0))
        cmds.append(DrawLine(
            0, self.bottom, getWidth(),
            self.bottom, "black", 1))
        
        cmds.append(DrawOutline(self.newtab_rect, "black", 1))
        cmds.append(DrawText(
            self.newtab_rect.left + self.padding,
            self.newtab_rect.top,
            "+", self.font, "black"))
        
        for i, tab in enumerate(self.browser.tabs):
            bounds = self.tab_rect(i)
            cmds.append(DrawLine(
                bounds.left, 0, bounds.left, bounds.bottom,
                "black", 1))
            cmds.append(DrawLine(
                bounds.right, 0, bounds.right, bounds.bottom,
                "black", 1))
            cmds.append(DrawText(
                bounds.left + self.padding, bounds.top + self.padding,
                "Tab {}".format(i), self.font, "black"))
        
            if tab == self.browser.active_tab:
                cmds.append(DrawLine(
                    0, bounds.bottom, bounds.left, bounds.bottom,
                    "black", 1))
                cmds.append(DrawLine(
                    bounds.right, bounds.bottom,
                    getWidth(), bounds.bottom,
                    "black", 1))
        
        cmds.append(DrawOutline(self.back_rect, "black", 1))
        cmds.append(DrawText(
            self.back_rect.left + self.padding,
            self.back_rect.top,
            "<", self.font, "black"))
        
        cmds.append(DrawOutline(self.back_rect, "black", 1))
        
        if str(self.browser.active_tab.url) in self.browser.bookmarks:
            cmds.append(DrawRect(self.bookmarks_rect, "yellow", 0))
        cmds.append(DrawRect(self.bookmarks_rect, None, 1))
        
        if self.browser.active_tab.locked:
            cmds.append(DrawText(
                self.address_rect.left + self.padding,
                self.address_rect.top,
                "\N{lock}", self.font, "black"))
        
        cmds.append(DrawOutline(self.address_rect, "black", 1))
        if self.focus == "address bar":
            cmds.append(DrawText(
                self.address_rect.left + self.padding,
                self.address_rect.top,
                self.address_bar, self.font, "black"))
            w = self.font.measure(self.address_bar)
            cmds.append(DrawLine(
                self.address_rect.left + self.padding + w,
                self.address_rect.top,
                self.address_rect.left + self.padding + w,
                self.address_rect.bottom,
                "red", 1))
        else:
            url = str(self.browser.active_tab.url)
            cmds.append(DrawText(
                self.address_rect.left + self.padding,
                self.address_rect.top,
                url, self.font, "black"))
            
        return cmds        
        
if __name__ == "__main__":
    import sys
    Browser().new_tab(URL(sys.argv[1]))
    tkinter.mainloop()
