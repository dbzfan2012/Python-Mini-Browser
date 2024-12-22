import tkinter
import tkinter.font
import sys
import math
from parameters import *
from htmlparser import *
from draw_commands import *
 
FONTS = dict()
def get_font(size, weight, style, family):
    key = (size, weight, style, family)
    if key not in FONTS:
        font = tkinter.font.Font(size=size, weight=weight, slant=style, family=family)
        label = tkinter.Label(font=font)
        FONTS[key] = (font, label)
    return FONTS[key][0]

def paint_tree(layout_object, display_list):
    if layout_object.should_paint():
        display_list.extend(layout_object.paint())
    
    for child in layout_object.children:
        paint_tree(child, display_list)

class DocumentLayout:
    def __init__(self, node): #node is an html parser node
        self.node = node
        self.parent = None
        self.children = []
        
        self.x = None
        self.y = None
        self.width = None
        self.height = None
        
    def __repr__(self):
        return "DocumentLayout()"
        
    def layout(self):
        child = BlockLayout(self.node, self, None)
        self.children.append(child)
        
        self.width = getWidth() - 2 * hstep()
        
        self.x = hstep()
        self.y = vstep()
        
        child.layout()
        
        self.height = child.height
        
        #self.display_list = child.display_list      
        
    def paint(self):
        return []  
    
    def should_paint(self):
        return True
        
BLOCK_ELEMENTS = [
    "html", "body", "article", "section", "nav", "aside",
    "h1", "h2", "h3", "h4", "h5", "h6", "hgroup", "header",
    "footer", "address", "p", "hr", "pre", "blockquote",
    "ol", "ul", "menu", "li", "dl", "dt", "dd", "figure",
    "figcaption", "main", "div", "table", "form", "fieldset",
    "legend", "details", "summary"
]

class BlockLayout:      
    def __init__(self, node, parent, previous, more_nodes = None): 
        # self.node = node
        # self.parent = parent
        # self.previous = previous
        # self.children = []
        
        # self.more_nodes = more_nodes
        
        # self.x = None
        # self.y = None
        # self.width = None
        # self.height = None
        
        # self.in_list = False
        # self.old_y = 0
        
        # self.display_list = []
        
        self.node = node
        self.parent = parent
        self.previous = previous
        self.children = []
        self.x = None
        self.y = None
        self.width = None
        self.height = None
        self.display_list = []
        
    def __repr__(self):
        return "BlockLayout(x={}, y={}, width={}, height={})".format(self.x, self.y, self.width, self.height)
        
    def layout_mode(self):
        if isinstance(self.node, Text):
            return "inline"
        elif any([ isinstance(child, Element) and \
                   child.tag in BLOCK_ELEMENTS
                  for child in self.node.children ]):
            return "block"
        elif self.node.children or self.node.tag == "input":
            return "inline"
        else:
            return "block"
        
    def processDimension(self, node, attribute):
        attr = node.style.get(attribute)
        if attr and attr.endswith("px"):
            value = float(attr[:-2])
            if (value < 0):
                node.style[attribute] = "auto"
            else:
                node.style[attribute] = value
            
        
    def layout(self):                
        self.x = self.parent.x
        self.width = self.parent.width
        
        if self.previous:
            self.y = self.previous.y + self.previous.height
        else:
            self.y = self.parent.y
            
        mode = self.layout_mode()      
        if mode == "block": #block case, #builds tree before layout nodes
            previous = None
            for child in self.node.children:
                # if isinstance(child, Element) and child.tag == "head":
                #     continue
                block = BlockLayout(child, self, previous)
                self.children.append(block)
                previous = block
        else:               
            self.new_line()
            self.recurse(self.node)
            #self.flush()
            
        for child in self.children:
            child.layout()
            
        self.height = sum([ child.height for child in self.children ])
        
        for child in self.children.copy():
            if child.height == 0 and len(child.children) > 0:
                if isinstance(child.children[0], LineLayout) and child.children[0].height == 0:
                    self.children.remove(child)

    def paint(self):
        cmds = []
                                
        bgcolor = self.node.style.get("background-color", "transparent")
        if bgcolor != "transparent":
            x2, y2 = self.x + self.width, self.y + self.height
            rect = DrawRect(self.self_rect(), bgcolor, 1)
            cmds.append(rect)
            
        return cmds
    
    def self_rect(self):
        x, y, w, h = self.x, self.y, self.width, self.height
        return Rect(x, y, x + w, y + h)
    
    def should_paint(self):
        return isinstance(self.node, Text) or \
            (self.node.tag != "input" and self.node.tag != "button")
        
    def recurse(self, tree):
        if isinstance(tree, Text):
            for word in tree.text.split():
                self.word(tree, word)
        else:
            if tree.tag == "br":
                self.new_line()
            elif tree.tag == "input" or tree.tag == "button":
                self.input(tree)
            else:
                for child in tree.children:
                    self.recurse(child)
            
    def new_line(self):
        self.cursor_x = 0
        last_line = self.children[-1] if self.children else None
        new_line = LineLayout(self.node, self, last_line)
        self.children.append(new_line)    
        
    def input(self, node): #undo indents      
        w = INPUT_WIDTH_PX
        if self.cursor_x + w > self.width:
            self.new_line()
        line = self.children[-1]
        previous_word = line.children[-1] if line.children else None
        input = InputLayout(node, line, previous_word)
        line.children.append(input)

        weight = node.style["font-weight"]
        style = node.style["font-style"]
        if style == "normal": style = "roman"
        size = int(float(node.style["font-size"][:-2]) * .75)
        font = get_font(size, weight, style, None)

        self.cursor_x += w + font.measure(" ")
        
    def word(self, node, word): #undo indents      
        weight = node.style["font-weight"]
        style = node.style["font-style"]
        if style == "normal": style = "roman"
        size = int(float(node.style["font-size"][:-2]) * 0.75)
        family = node.style["font-family"]
        font = get_font(size, weight, style, family)                        
        
        w = font.measure(word)

        if self.cursor_x + w > self.width:
            self.new_line()
                
        line = self.children[-1]
        previous_word = line.children[-1] if line.children else None
        text = TextLayout(node, word, line, previous_word)
        line.children.append(text)
        self.cursor_x += w + font.measure(" ")
            
    # # flush is for resetting the lines
    # def flush(self):
    #     if not self.line: return
    #     metrics = [font.metrics() for x, word, font, color, super, abbr in self.line]
    #     max_ascent = max([metric["ascent"] for metric in metrics])
    #     baseline = self.cursor_y + 1.25 * max_ascent
        
    #     # later this could cause problem if the tuple is adjusted
    #     font = self.line[-1][2]
    #     line_len = self.cursor_x - font.measure(" ") - hstep()  #HSTEP is padding
    #     padding = ((getWidth() - line_len) // 2) - hstep()
        
    #     #total_height = 1.25 * max_ascent + 1.25 * max_descent
    #     for rel_x, word, font, color, super, abbr in self.line:
    #         x = self.x + rel_x
    #         y = self.y + baseline - font.metrics("ascent")
    #         if (self.center):
    #             x += padding
    #         if (super):
    #             y = baseline - max_ascent             
    #         self.display_list.append((x, y, word, font, color))
            
    #     max_descent = max(metric["descent"] for metric in metrics)
    #     self.cursor_y = baseline + 1.25 * max_descent
        
    #     self.cursor_x = hstep() #CHANGE TO 0? probably not?
    #     self.line = []

class LineLayout:
    def __init__(self, node, parent, previous):
        self.node = node
        self.parent = parent
        self.previous = previous
        self.children = []
        self.x = None
        self.y = None
        self.width = None
        self.height = None
        
    def __repr__(self):
        return "LineLayout(x={}, y={}, width={}, height={})".format(self.x, self.y, self.width, self.height)
        
    def should_paint(self):
        return True
        
    def layout(self):
        self.width = self.parent.width
        self.x = self.parent.x

        if self.previous:
            self.y = self.previous.y + self.previous.height
        else:
            self.y = self.parent.y

        for word in self.children:
            word.layout()

        if not self.children:
            self.height = 0
            return

        max_ascent = max([word.font.metrics("ascent") 
                          for word in self.children])
        baseline = self.y + 1.25 * max_ascent
        for word in self.children:
            word.y = baseline - word.font.metrics("ascent")
        max_descent = max([word.font.metrics("descent")
                           for word in self.children])
        self.height = 1.25 * (max_ascent + max_descent)
            
    def paint(self):
        return []
            
        
class TextLayout:
    def __init__(self, node, word, parent, previous):
        self.node = node
        self.word = word
        self.children = []
        self.parent = parent
        self.previous = previous
        self.x = None
        self.y = None
        self.width = None
        self.height = None
        self.font = None
        
    def __repr__(self):
        return "TextLayout(x={}, y={}, width={}, height={}, word={})".format(self.x, self.y, self.width, self.height, self.word)
        
    def layout(self):
        weight = self.node.style["font-weight"]
        style = self.node.style["font-style"]
        if style == "normal": style = "roman"
        size = int(float(self.node.style["font-size"][:-2]) * .75)
        family = self.node.style["font-family"]
        self.font = get_font(size, weight, style, family)

        self.width = self.font.measure(self.word)

        if self.previous:
            space = self.previous.font.measure(" ")
            self.x = self.previous.x + space + self.previous.width
        else:
            self.x = self.parent.x

        self.height = self.font.metrics("linespace")
        
    def paint(self):
        color = self.node.style["color"]
        return [DrawText(self.x, self.y, self.word, self.font, color)]

    def should_paint(self):
        return True

INPUT_WIDTH_PX = 200

class InputLayout:
    def __init__(self, node, parent, previous):
        self.node = node
        self.children = []
        self.parent = parent
        self.previous = previous
        self.x = None
        self.y = None
        self.width = None
        self.height = None
        self.font = None
        
        self.hide_password = False
        
    def __repr__(self):
        if self.node.tag == "input" and self.node.attributes.get("type", "text") == "checkbox":
            if "checked" in self.node.attributes:
                extra = ", checked"
            else:
                extra = ", unchecked"
        else:
            extra = ""
        return "InputLayout(x={}, y={}, width={}, height={}, tag={}{})".format(
            self.x, self.y, self.width, self.height, self.node.tag, extra)
        
    def should_paint(self):
        return True
        
    def layout(self):
        weight = self.node.style["font-weight"]
        style = self.node.style["font-style"]
        if style == "normal": style = "roman"
        size = int(float(self.node.style["font-size"][:-2]) * .75)
        family = self.node.style["font-family"]
        self.font = get_font(size, weight, style, family)

        self.width = INPUT_WIDTH_PX

        if self.previous:
            space = self.previous.font.measure(" ")
            self.x = self.previous.x + space + self.previous.width
        else:
            self.x = self.parent.x

        self.height = self.font.metrics("linespace")
        
        if self.node.attributes.get('type', '') == "hidden":
            self.height = 0.0
            self.width = 0.0
            
        if self.node.attributes.get('type', '') == "password":
            self.hide_password = True
        
        if self.node.attributes.get('type', '') == "checkbox":
            self.height = 16
            self.width = 16
        
        # if "button" in str(self.node):
        #     #create block layout for button
            
        #     button_layout = BlockLayout(self.node, self.parent, self.previous, [])
        #     button_layout.x = self.x
        #     button_layout.y = self.y
        #     button_layout.height = self.height
        #     button_layout.width = self.width
            
            
        #     line = self.children[-1] if len(self.children) > 0 else None
        #     line.children.append(button_layout)
            
            #print(button_layout)
            #self.node.children.append(button_layout)
    
    def paint(self):
        cmds = []        
        bgcolor = self.node.style.get("background-color", "transparent")
        
        # sets color to blue
        if self.node.attributes.get("checked"):
            bgcolor = "blue"
            
        if bgcolor != "transparent":
            x2, y2 = self.x + self.width, self.y + self.height
            rect = DrawRect(self.self_rect(), bgcolor, 1)
            cmds.append(rect)
                        
        if self.node.tag == "input":
            text = self.node.attributes.get("value", "")
        elif self.node.tag == "button":
            if len(self.node.children) == 1 and \
                isinstance(self.node.children[0], Text):
                    text = self.node.children[0].text
            else:
                print("Ignoring HTML contents inside button")
                text = ""        
        color = self.node.style["color"]
        if self.hide_password:
            hidden_text = "*" * len(text)
            cmds.append(DrawText(self.x, self.y, hidden_text, self.font, color))
        else:
            cmds.append(DrawText(self.x, self.y, text, self.font, color))
        
        if self.node.is_focused:
            cx = self.x + self.font.measure(text)
            cmds.append(DrawLine(
                cx, self.y, cx, self.y + self.height, "black", 1))
        
        return cmds
    
    def self_rect(self):
        x, y, w, h = self.x, self.y, self.width, self.height
        return Rect(x, y, x + w, y + h)

        
