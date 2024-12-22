import sys

class Text:
    def __init__(self, text, parent):
        self.text = text
        self.children = []
        self.parent = parent
        self.is_focused = False
        
    def __repr__(self):
        #return "Text('{}')".format(self.text)
        return repr(self.text)
    
class Element:
    def __init__(self, tag, attributes, parent):
        self.tag = tag
        self.attributes = attributes
        self.children = []
        self.parent = parent
        self.is_focused = False

    def __repr__(self):
        attrs = [" " + k + "=\"" + v + "\"" for k, v  in self.attributes.items()]
        attr_str = ""
        for attr in attrs:
            attr_str += attr
        return "<" + self.tag + attr_str + ">"
    
def print_tree(node, indent=0):
    print(" " * indent, node)
    for child in node.children:
        print_tree(child, indent + 2)
    
class HTMLParser:
    SELF_CLOSING_TAGS = [
        "area", "base", "br", "col", "embed", "hr", "img", "input",
        "link", "meta", "param", "source", "track", "wbr"
    ]
    
    HEAD_TAGS = [
        "base", "basefont", "bgsound", "noscript",
        "link", "meta", "title", "style", "script"    
    ] #in book!
    
    def __init__(self, body):
        self.body = body
        self.unfinished = [] #list of unfinished nodes
        # self.in_comment = False
        # self.whitespace = "abcflkjkajdlkasjdlkasjd"

        # self.in_script = False
        # self.new_delimiter_equals = "thisisanewdelimiterforequals"
        # self.new_delimiter_whitespace = "thisisanewdelimiterforwhitespace"
                
    def parse(self):
        text = ""
       # print("START: <" + self.body + "> FINISH", file=sys.stderr)
        in_tag = False
        for c in self.body:
            if c == "<":
                in_tag = True
                if text: self.add_text(text)
                text = ""
            elif c == ">":
                in_tag = False
                self.add_tag(text)
                text = ""
            else:
                text += c
        if not in_tag and text:
            self.add_text(text)
        return self.finish()
    
    # def parse(self): #lex def (roughly) - break something into lexical chunks
    #     text = ""
    #     in_comment = False
    #     in_tag = False
        
    #     in_script = False
    #     in_tag_attr = False
    #     in_tag_attr_equaled = False
    #     in_tag_attr_quote = False
    #     tag_quote = False
        
    #     for i, c in enumerate(self.body):
            
    #         if in_comment:
    #             if self.body[i-3:i] == '-->' and self.body[i-5:i] != '<!-->' and self.body[i-6:i] != '<!--->':
    #                 in_comment = False
    #             else:
    #                 continue
                
    #         if in_script:
    #             in_script = self.body[i:i+9] != "</script>"
    #         # if in_tag:
    #         #     if c == "=" and text and not self.body[i-1].isspace():
    #         #         in_tag_attr = True
    #         #         in_tag_attr_equaled = True
    #         #         in_tag = False
    #         #         c = self.new_delimiter_equals
    #         #     elif c == " " and text.strip():
    #         #         in_tag_attr = True
    #         #         in_tag = False
    #         #         c = self.new_delimiter_whitespace
    #         # elif in_tag_attr:
    #         #     if c in "\"\'":
    #         #         in_tag_attr = False
    #         #         in_tag_attr_quote = True
    #         #         tag_quote = c
    #         #     elif c == ">":
    #         #         in_tag_attr = False
    #         #     elif c == " ":
    #         #         in_tag_attr = False
    #         #         in_tag = True
    #         #         c = self.new_delimiter_whitespace
    #         #     elif c == "=" and not in_tag_attr_equaled and not self.body[i-1].isspace():
    #         #         c = self.new_delimiter_equals
    #         #         in_tag_attr_equaled = True
    #         # elif in_tag_attr_quote:
    #         #     if c == tag_quote and self.body[i-1:i] != "\\":
    #         #         in_tag_attr_quote = False
    #         #         in_tag = True
    #         #         if self.body[i+1] != ">":
    #         #             c += self.new_delimiter_whitespace
    #         #     elif c == ">":
    #         #         in_tag_attr_quote = False
    #         #     elif c == " ":
    #         #         pass
    #         if c == "<" and not in_script and not in_tag_attr and not in_tag_attr_quote:
    #             if self.body[i:i+4] == '<!--':
    #                 in_comment = True
    #                 if text:
    #                     self.add_text(text)
    #                 text = ''
    #                 continue
    #             in_tag = True
    #             if text: 
    #                 self.add_text(text) # add_text to add later
    #             text=""
    #         elif c == ">" and not in_script and not in_tag_attr and not in_tag_attr_quote:
    #             in_tag = False
    #             self.add_tag(text) #add_tag to add later
    #             if text == "script":
    #                 in_script = True
    #             text=""
    #         else:
    #             text += c
    #     if not in_tag and text:
    #         self.add_text(text)
    #     return self.finish() #for cleanup, to add later
    
    # def get_attributes(self, text):
    #     parts = text.split(self.new_delimiter_whitespace)
    #     tag = parts[0].casefold().replace(self.new_delimiter_equals, "=")
    #     attributes = {}
    #     for attrpair in parts[1:]: #:1 means list starting from one (excluding first)
    #         if attrpair == "=": continue
    #         if self.new_delimiter_equals in attrpair:
    #             key, value = attrpair.split(self.new_delimiter_equals, 1) #only first occurrence
    #             if len(value) > 2 and value[0] in ["'", "\""]:
    #                 value = value[1:-1]
                    
    #             attributes[key.casefold()] = value.replace(self.new_delimiter_whitespace, " ")
    #         else:
    #             attributes[attrpair.casefold()] = ""
    #     return tag, attributes
    
    def get_attributes(self, text):
        parts = text.split()
        tag = parts[0].casefold()
        attributes = {}
        for attrpair in parts[1:]:
            if "=" in attrpair:
                key, value = attrpair.split("=", 1)
                if len(value) > 2 and value[0] in ["'", "\""]:
                    value = value[1:-1]
                attributes[key.casefold()] = value
            else:
                attributes[attrpair.casefold()] = ""
        return tag, attributes
    
    def add_text(self, text):
        if text.isspace(): return
        self.implicit_tags(None)
        parent = self.unfinished[-1]
        node = Text(text, parent)
        parent.children.append(node)    
        
    # def add_tag(self, tag):        
    #     tag, attributes = self.get_attributes(tag)
    #     if tag.startswith("!"): return
    #     self.implicit_tags(tag) #add method later

    #     if tag == "script":
    #         self.in_script = True
        
    #     open_tags = [node.tag for node in self.unfinished]
        
    #     if tag.startswith("/"):
    #         if len(self.unfinished) == 1: return #returns if only one element in unfinished
    #         node = self.unfinished.pop()
    #         parent = self.unfinished[-1]
    #         parent.children.append(node)
    #     elif tag in self.SELF_CLOSING_TAGS:
    #         parent = self.unfinished[-1]
    #         node = Element(tag, attributes, parent)
    #         parent.children.append(node)
    #     elif tag == "p" and "p" in open_tags:
    #         rebuild_tags = list()
    #         last_tag = self.unfinished.pop()
    #         while last_tag.tag != 'p':
    #             rebuild_tags.append(last_tag)
    #             grandparent = self.unfinished[-1]
    #             grandparent.children.append(last_tag)
    #             last_tag = self.unfinished.pop()
                
    #         grandparent = self.unfinished[-1]
    #         grandparent.children.append(last_tag)
            
    #         t, attributes = self.get_attributes(tag)
    #         parent_node = Element(t, parent=grandparent, attributes=attributes)
    #         self.unfinished.append(parent_node)
            
    #         for node in rebuild_tags:
    #             parent = self.unfinished[-1] 
    #             rebuild_node = Element(node.tag, parent=parent, attributes=node.attributes)
    #             self.unfinished.append(rebuild_node)                          
    #     else:
    #         parent = self.unfinished[-1] if self.unfinished else None #sets to None if unfinished is empty
    #         node = Element(tag, attributes, parent)
    #         self.unfinished.append(node) #add at the end, for now keep on stack/unfinished list
            
    def add_tag(self, tag):
        tag, attributes = self.get_attributes(tag)
        if tag.startswith("!"): return
        self.implicit_tags(tag)

        if tag.startswith("/"):
            if len(self.unfinished) == 1: return
            node = self.unfinished.pop()
            parent = self.unfinished[-1]
            parent.children.append(node)
        elif tag in self.SELF_CLOSING_TAGS:
            parent = self.unfinished[-1]
            node = Element(tag, attributes, parent)
            parent.children.append(node)
        else:
            parent = self.unfinished[-1] if self.unfinished else None
            node = Element(tag, attributes, parent)
            self.unfinished.append(node)
        
    def finish(self):
        if not self.unfinished:
            self.implicit_tags(None)
        while len(self.unfinished) > 1:
            node = self.unfinished.pop()
            parent = self.unfinished[-1]
            parent.children.append(node)
        return self.unfinished.pop()
    
    # def implicit_tags(self, tag):
    #     while True:
    #         open_tags = [node.tag for node in self.unfinished]
            
    #         if open_tags == [] and tag != "html":
    #             self.add_tag("html") #adds html tag to top of tree
    #         elif open_tags == ["html"] \
    #              and tag not in ["head", "body", "/html"]:
    #             if tag in self.HEAD_TAGS:
    #                 self.add_tag("head")
    #             else:
    #                 self.add_tag("body")
    #         elif open_tags == ["html", "head"] and \
    #              tag not in ["/head"] + self.HEAD_TAGS:
    #             self.add_tag("/head")
    #         else:
    #             break
            
    def implicit_tags(self, tag):
        while True:
            open_tags = [node.tag for node in self.unfinished]
            if open_tags == [] and tag != "html":
                self.add_tag("html")
            elif open_tags == ["html"] \
                 and tag not in ["head", "body", "/html"]:
                if tag in self.HEAD_TAGS:
                    self.add_tag("head")
                else:
                    self.add_tag("body")
            elif open_tags == ["html", "head"] and \
                 tag not in ["/head"] + self.HEAD_TAGS:
                self.add_tag("/head")
            else:
                break
                    