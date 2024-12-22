console = { log: function(x) { call_python("log", x); },
            error: function(x) {call_python("error", x);} }

document = { querySelectorAll: function(s) {
    var handles = call_python("querySelectorAll", s);
    return handles.map(function(h) { return new Node(h) });
}, 
    createElement: function(tag) {
        var handle = call_python("createElement", tag);
        return new Node(handle);
}}


// Object.defineProperty(document.prototype, "cookie", {
//     set: function() {
//         return call_python("getCookie");
//     }
// });

function Node(handle) { this.handle = handle; this.children = []; }

Node.prototype.getAttribute = function(attr) {
    return call_python("getAttribute", this.handle, attr);
}

Node.prototype.appendChild = function(child) {
    return call_python("appendChild", this.handle, child.handle);
}

Node.prototype.insertBefore = function(element, before) {
    var handle = -1;
    if (before != null) {
        handle = before.handle;
    }
    return call_python("insertBefore", this.handle, element.handle, handle);
}

LISTENERS = {}

function Event(type) {
    this.type = type
    this.do_default = true;
    this.stop_propagation = false;
}

Event.prototype.preventDefault = function() {
    this.do_default = false;
}

Event.prototype.stopPropagation = function() {
    this.stop_propagation = true;
}

Node.prototype.addEventListener = function(type, listener) {
    if (!LISTENERS[this.handle]) LISTENERS[this.handle] = {};
    var dict = LISTENERS[this.handle];
    if (!dict[type]) dict[type] = [];
    var list = dict[type];
    list.push(listener);
}

Object.defineProperty(Node.prototype, 'innerHTML', {
    set: function(s) {
        call_python("innerHTML_set", this.handle, s.toString());
    }
});

function handle_to_nodes(handles) {
    return handles.map(function(h) {return new Node(h)});
}

Object.defineProperty(Node.prototype, 'children', {
    get: function() {
        return handle_to_nodes(call_python("getChildren", this.handle));
    }
});

Node.prototype.dispatchEvent = function(evt) {
    var type = evt.type;
    var handle = this.handle;

    while (handle != -1 && !evt.stop_propagation) {
        var list = (LISTENERS[handle] && LISTENERS[handle][type]) || [];
        if (evt.stop_propagation) {
            break;
        }
        for (var i = 0; i < list.length; i++) {
            list[i].call(this, evt);
        }
        if (evt.do_default) {
            break;
        }
        handle = call_python("getParent", handle);
    }
    return evt.do_default;
}

function XMLHttpRequest() {}

XMLHttpRequest.prototype.open = function(method, url, is_async) {
    if (is_async) throw Error("Asynchronous XHR is not supported");
    this.method = method;
    this.url = url;
}

XMLHttpRequest.prototype.send = function(body) {
    this.responseText = call_python("XMLHttpRequest_send",
        this.method, this.url, body);
}