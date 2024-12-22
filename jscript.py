import dukpy
import sys

from cssparser import *
from htmlparser import *
from url import *

def tree_to_list(tree, list):
    list.append(tree)
    for child in tree.children:
        tree_to_list(child, list)
    return list
  
RUNTIME_JS = open("runtime.js").read()

EVENT_DISPATCH_JS = \
    "new Node(dukpy.handle).dispatchEvent(new Event(dukpy.type))"
    
VARS = []

class JSContext:
  def __init__(self, tab):
    self.tab = tab
    self.interp = dukpy.JSInterpreter()
        
    self.node_to_handle = {}
    self.handle_to_node = {}
    
    self.interp.export_function("getParent", self.getParent)
    self.interp.export_function("log", print)
    self.interp.export_function("error", self.error)
    self.interp.export_function("querySelectorAll", 
      self.querySelectorAll)
    self.interp.export_function("getAttribute",
            self.getAttribute)
    self.interp.export_function("innerHTML_set", self.innerHTML_set)
    self.interp.export_function("createElement", self.createElement)
    self.interp.export_function("appendChild", self.appendChild)
    self.interp.export_function("insertBefore", self.insertBefore)
    self.interp.export_function("getChildren", self.getChildren)
    self.interp.export_function("XMLHttpRequest_send", self.XMLHttpRequest_send)
    self.interp.export_function("getCookie", self.getCookie)
    with open("runtime.js") as f:
            self.interp.evaljs(RUNTIME_JS)
            
  def getCookie(self):
    print("HELLO MY NAME IS OBI WAN KENOBI:", COOKIE_JAR)
    if len(COOKIE_JAR) == 0:
      return "<BLANKLINE>"
            
  def XMLHttpRequest_send(self, method, url, body):
        full_url = self.tab.url.resolve(url)
        if not self.tab.allowed_request(full_url):
            raise Exception("Cross-origin XHR blocked by CSP")
        headers, out = full_url.request(self.tab.url, body)
        if full_url.origin() != self.tab.url.origin():
            raise Exception("Cross-origin XHR request not allowed")
        return out
    
  def error(self, error):
    #print("The tree is: <")
    print_tree(self.tab.nodes)
    print(error, file=sys.stderr)
    #print(">")
    
  def run(self, code):
    return self.interp.evaljs(code)
  
  def dispatch_event(self, type, elt):
    node = elt
    while node:
      handle = self.node_to_handle.get(node, -1)
      do_default = self.interp.evaljs(
          EVENT_DISPATCH_JS, type=type, handle=handle)
      if not do_default:
        break
      node = node.parent
    return not do_default
  
  def getParent(self, handle):
    node = self.handle_to_node[handle]
    parent = node.parent
    
    if parent:
      return self.get_handle(parent)
    
    return -1
  
  def idsToVars(self, ids):
    for node in ids:
      id = node.attributes.get("id")
      handle = self.get_handle(node)
      add_var = id + " = new Node(" + str(handle) + ")"
      self.run(add_var)
      VARS.append(id)
  
  def querySelectorAll(self, selector_text):
    selector = CSSParser(selector_text).selector()
    
    nodes = [node for node in tree_to_list(self.tab.nodes, [])
                  if selector.matches(node)] 
    
    nodes_return = [self.get_handle(node) for node in nodes]
        
    return nodes_return  
    
  def getChildren(self, parent):
    parent_node = self.handle_to_node[parent]
    return [self.get_handle(child) for child in parent_node.children if isinstance(child, Element)]
  
  def createElement(self, tag):
    new_elt = Element(tag, {}, None)
    handle = self.get_handle(new_elt)
    return handle
  
  def appendChild(self, parent, child): #parent, child is a handle
    node_parent = self.handle_to_node[parent]
    node_child = self.handle_to_node[child]
    node_child.parent = node_parent
    node_parent.children.append(node_child)
  
  def insertBefore(self, parent, element, before):
    node_parent = self.handle_to_node[parent]
    node_element = self.handle_to_node[element]
    node_element.parent = node_parent
    if (before == -1):
      node_parent.children.append(node_element)
    else:
      node_before = self.handle_to_node[before]  
      for i, node in enumerate(node_parent.children):
        if node == node_before:
          node_parent.children.insert(i, node_element)
          break     
    
  def get_handle(self, elt):
    if elt not in self.node_to_handle:
      handle = len(self.node_to_handle)
      self.node_to_handle[elt] = handle
      self.handle_to_node[handle] = elt
    else:
      handle = self.node_to_handle[elt]
    return handle

  def getAttribute(self, handle, attr):
    elt = self.handle_to_node[handle]
    attr = elt.attributes.get(attr, None)
    return attr if attr else ""
  
  def innerHTML_set(self, handle, s):   
    doc = HTMLParser("<html><body>" + s + "</body></html>").parse()
    
    new_vars = []
    
    new_nodes = doc.children[0].children
    elt = self.handle_to_node[handle]
    
    if isinstance(elt, Element) and elt.attributes.get("id"):
      id = elt.attributes.get("id")
      var_node = id + " = new Node(" + str(handle) + ")"
      self.run(var_node)
      new_vars.append(id)
      if id not in VARS: VARS.append(id)
        
    elt.children = new_nodes
    for child in elt.children:
      if (isinstance(child, Element) and child.attributes.get("id")):
        id = child.attributes.get("id")
        var_node = id + " = new Node(" + str(self.get_handle(child)) + ")"
        self.run(var_node)
        new_vars.append(id)
        if id not in VARS: VARS.append(id)
      child.parent = elt
    
    for var in VARS:
      if var not in new_vars:
        self.run("delete " + var)

    VARS.clear()
    for var in new_vars:
      VARS.append(var)
        
    self.tab.render()  
    