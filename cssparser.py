# CSS Grammer
# css file := sequence of rules
# rule := a guard, a selector, '{', a body, '}'
# body := a sequence of pairs separated by ';'
# pair := word ':' word
# word := a sequence of alphanumeric characters or '#', '-', '.', or '%'

# Example css line
# s = "background-color: lightblue;font-size: 12px;"
#every pair ends with a semicolon, even the last one
# s = "background-color: lightblue; margin: 1px 2px; font-size: 12px" -> our parser doesn't support margin with two values

from htmlparser import Element
import sys

INHERITED_PROPERTIES = {
    "font-size": "16px",
    "font-style": "normal",
    "font-weight": "normal",
    "color": "black",
    "font-family": "Times"
}

def cascade_priority(rule):
  selector, body = rule
  return selector.priority

class DescendantSelector:
  def __init__(self, ancestor, descendant):
    self.ancestor = ancestor
    self.descendant = descendant
    self.priority = ancestor.priority + descendant.priority
    
  def matches(self, node):
    if not self.descendant.matches(node): return False
    while node.parent:
      if self.ancestor.matches(node.parent): return True
      node = node.parent
    return False
  
  def __repr__(self):
        return ("DescendantSelector(ancestor={}, descendant={}, priority={})") \
            .format(self.ancestor, self.descendant, self.priority)
            
class ClassSelector:
  def __init__(self, classname):
    self.priority = 10
    self.classname = classname
  
  def matches(self, node):
    if isinstance(node, Element) and "class" in node.attributes:
      classes = node.attributes["class"].split(" ")
      return self.classname in classes
    return False
  
  def __repr__(self):
        return "ClassSelector(classname={}, priority={})".format(
            self.classname, self.priority)


class TagSelector:
  def __init__(self, tag):
    self.tag = tag
    self.priority = 1
    
  def matches(self, node):
    return isinstance(node, Element) and self.tag == node.tag

  def __repr__(self):
        return "TagSelector(tag={}, priority={})".format(
            self.tag, self.priority)

class CSSParser:
  def __init__(self, s):
    self.s = s #string
    self.i = 0 #index, progress through the string
    
  def whitespace(self):
    while self.i < len(self.s) and self.s[self.i].isspace():
      self.i += 1
      
  def literal(self, literal):
    if not (self.i < len(self.s) and self.s[self.i] == literal):
      raise Exception("Parsing error")
    self.i += 1
    
  #parse through a word
  def word(self):
    start = self.i
    while self.i < len(self.s):
      char = self.s[self.i]
      if char.isalnum() or char in "#-.%": # is alpha numeric or one of symbols
        self.i += 1
      else:
        break
    if not (self.i > start):
      raise Exception("Parsing error")
    return self.s[start:self.i]
      
      
  # pair := word ':' word
  def pair(self):
    prop = self.word() #property of the pair
    self.whitespace()
    self.literal(":")
    self.whitespace()
    if (prop.casefold() == "font"):
      val = ""
      while self.s[self.i] != ";":
        val += self.s[self.i]
        self.i += 1
    else:
      val = self.word()
    return prop.casefold(), val
  
  def ignore_until(self, chars):
    while self.i < len(self.s):
      if self.s[self.i] in chars:
        return self.s[self.i]
      else:
        self.i += 1
    return None
  
  #parses the font shorthand
  def parseShortcut(self, pairs, val):
    if (len(val) == 1):
      pairs["font-family"] = val[0]
    if (len(val) == 2):
      pairs["font-size"] = val[0]
      pairs["font-family"] = val[1]
    if (len(val) == 3):
      if (val[0] == "italic"):
        pairs["font-style"] = val[0]
      else:
        pairs["font-weight"] = val[0]
      pairs["font-size"] = val[1]
      pairs["font-family"] = val[2]
    if (len(val) >= 4):
      pairs["font-style"] = val[0]
      pairs["font-weight"] = val[1]
      pairs["font-size"] = val[2]
      new_family = ""
      for i in range(3, len(val) - 1):
        new_family += val[i] + " "
      new_family += val[-1]
      pairs["font-family"] = new_family
    return pairs
    
  def body(self):
    pairs = {}
    while self.i < len(self.s) and self.s[self.i] != "}":
      try:
        prop, val = self.pair() #change parsing when getting shorthand?
        if (prop == "font"):
          val = val.split(" ")
          pairs = self.parseShortcut(pairs, val)
        else:
          pairs[prop.casefold()] = val # set prop we found to value we found
        self.whitespace() # ignores whitespace between pairs for us
        self.literal(";") # expect to see semicolon, move past it
        self.whitespace()
      except Exception:
        why = self.ignore_until([";", "}"])
        if why == ";":
          self.literal(";")
          self.whitespace()
        else:
          break
          
    return pairs
  
  def selector(self):
    word = self.word()
    if (word.startswith(".")):
      out = ClassSelector(word[1:])
    else:
      out = TagSelector(word.casefold())
    self.whitespace()
    while self.i < len(self.s) and self.s[self.i] != "{":
        tag = self.word()
        if (tag.startswith(".")):
          descendant = ClassSelector(tag[1:])
        else:
          descendant = TagSelector(tag.casefold())
        out = DescendantSelector(out, descendant)
        self.whitespace()
    return out
  
  def getClassname(self):
    idx = self.i
    classname = ""
    while self.s[idx].isalnum() or self.s[idx] in "#-.%":
      if (idx > len(self.s)):
        break
      classname += self.s[idx]
      idx += 1
    return classname
  
  def parse(self):
    rules = []
    while self.i < len(self.s):
      try:
        self.whitespace()
        selector = self.selector()
        self.literal("{")
        self.whitespace()
        body = self.body()
        self.literal("}")
        rules.append((selector, body))
      except Exception:
        why = self.ignore_until(["}"])
        if why == "}":
          self.literal("}")
          self.whitespace()
        else:
          break
    return rules
  
def style(node, rules):
  node.style = {}
  for property, default_value in INHERITED_PROPERTIES.items():
    if node.parent:
      node.style[property] = node.parent.style[property]
    else:
      node.style[property] = default_value
  for selector, body in rules:
    if not selector.matches(node): continue
    for property, value in body.items():
      node.style[property] = value
  if isinstance(node, Element) and "style" in node.attributes:
    pairs = CSSParser(node.attributes["style"]).body()
    for property, value in pairs.items():
      node.style[property] = value
  if node.style["font-size"].endswith("%"):
    if node.parent:
      parent_font_size = node.parent.style["font-size"]
    else:
      parent_font_size = INHERITED_PROPERTIES["font-size"]
    node_pct = float(node.style["font-size"][:-1]) / 100
    parent_px = float(parent_font_size[:-2])
    node.style["font-size"] = str(node_pct * parent_px) + "px"
  for child in node.children:
    style(child, rules)
  
  