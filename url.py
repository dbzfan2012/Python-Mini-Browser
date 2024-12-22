import time

import socket
import ssl #secure socket layer, helps with security
import sys

COOKIE_JAR = {}

class URL:
    
    cache = dict()
    
    def __init__(self, url):
        self.full_url = url
        self.fragment = None
        
        self.scheme, url = url.split("://", 1)
        assert self.scheme in ("file", "http", "https", "about") #equivalent to a double or
        
        if self.scheme == "file":
            self.port = None
            self.host = None
            self.path = url
        elif self.scheme == "about":
            self.port = None
            self.host = None
            self.path = url
        else:        
            if self.scheme == "http":
                self.port = 80
            elif self.scheme == "https":
                self.port = 443
            
            #normalizing url input, if no slash adds one to make next line work
            if ("/" not in url):
                url = url + "/"
            self.host, url = url.split("/", 1)
            self.path = "/" + url
            
            if "#" in self.path:
                split = self.path.split("#")
                self.path = split[0]
                self.fragment = split[1]
            
            #checks for formatting of port when given with :
            if ":" in self.host:
                self.host, port = self.host.split(":")
                self.port = int(port)
        
    def resolve(self, url):
        if "://" in url: return URL(url)
        if not url.startswith("/"):
            dir, _ = self.path.rsplit("/", 1)
            while url.startswith("../"):
                _, url = url.split("/", 1)
                if "/" in dir:
                    dir, _ = dir.rsplit("/", 1)
            url = dir + "/" + url
        if url.startswith("//"):
            return URL(self.scheme + ":" + url)
        else:
            return URL(self.scheme + "://" + str(self.host) + \
                       ":" + str(self.port) + url)
            
    def __str__(self):
        port_part = ":" + str(self.port)
        if self.scheme == "https" and self.port == 443:
            port_part = ""
        if self.scheme == "http" and self.port == 80:
            port_part = ""
        fragment_part = "" if self.fragment == None else "#" + self.fragment
        return self.scheme + "://" + str(self.host) + port_part + self.path + fragment_part
    
    def appendGet(self, body, get=False):
        self.path += "?" + body
        if get:
            self.path += "#THISSTATEMENTISFALSE#"
        
    def noBody(self):
        check = self.path
        check = check.split("&")
        if len(check) > 1:
            return False
        return True
    
    def origin(self):
        return self.scheme + "://" + self.host + ":" + str(self.port)
        
    #self, headers = None, redirect_limit = 0, payload=None
    def request(self, referrer, refer_policy=None, payload=None):    
        if self.scheme == "file":
            file = open(self.path, "r")
            body = file.read()
            return body
        elif self.scheme == "about" and self.path == "bookmarks":
            return "!bookmarks!"
        else:
            # if redirect_limit > 10:
            #     raise RedirectLoopError()
            
            s = socket.socket(
                family = socket.AF_INET,
                type   = socket.SOCK_STREAM,
                proto = socket.IPPROTO_TCP
            )
            
            #checks if url is in cache
            if self.full_url in URL.cache:
                #checks if item in cache is expired or not
                if time.time() >= URL.cache[self.full_url][1]:
                    del URL.cache[self.full_url]
                else:
                    return URL.cache[self.full_url][0]
            
            s.connect((self.host, self.port))
            
            if self.scheme == "https":
                ctx = ssl.create_default_context()
                try:
                    s = ctx.wrap_socket(s, server_hostname = self.host) #catch error here     
                except:
                    body = "<!doctype html>\nSecure Connection Failed"
                    return {}, body
            
            if payload:
                if self.path.endswith("#THISSTATEMENTISFALSE#"):
                    self.path = self.path.split("#THISSTATEMENTISFALSE#")[0]
                    method = "GET"
                else:
                    method = "POST"
            else:
                method = "GET"
                
            request = "{} {} HTTP/1.0\r\n".format(method, self.path)
            if payload and method == "POST":
                length = len(payload.encode("utf8"))
                request += "Content-Length: {}\r\n".format(length)
            
            request += "Host: {}\r\n".format(self.host)
            if self.host in COOKIE_JAR:
                cookie, params = COOKIE_JAR[self.host]
                allow_cookie = True
                if referrer and params.get("samesite", "none") == "lax":
                    if method != "GET":
                        allow_cookie = self.host == referrer.host
                if allow_cookie:
                    request += "Cookie: {}\r\n".format(cookie)
            request += "\r\n"
            
            # request_headers = dict()
            # request_headers["host"] = f"{self.host}\r\n"
            # request_headers["connection"] = "close\r\n"
            # request_headers["user-agent"] = "493\r\n"
            # if headers:
            #     for key, value in headers.items():
            #         request_headers[key.lower()] = value + "\r\n"
            # for key, value in request_headers.items():
            #     request += f"{key.title()}: {value}"
            # request += "\r\n"
            
            if payload and method == "POST": request += payload
            
            s.send(request.encode("utf8"))
            
            #Should not use industrially, because it waits a long time for the whole
            #response
            response = s.makefile("r", encoding = "utf8", newline = "\r\n")
            
            statusline = response.readline()
            version, status, explanation = statusline.split(" ", 2) #gets 1.0, 200, OK (as an example)
            
            response_headers = dict()
            while True:
                line = response.readline()
                if line == "\r\n": break
                header, value = line.split(":", 1)
                response_headers[header.casefold()] = value.strip() #.casefold() makes it either all cap or all lowercase
                
                
            
            if "set-cookie" in response_headers:
                cookie = response_headers["set-cookie"]
                params = {}
                if ";" in cookie:
                    cookie, rest = cookie.split(";", 1)
                    for param in rest.split(";"):
                        if '=' in param:
                            param, value = param.split("=", 1)
                        else:
                            value = "true"
                        params[param.strip().casefold()] = value.casefold()
                COOKIE_JAR[self.host] = (cookie, params)
                
            body = response.read()
            # if refer_policy == "no-referer":
            #     pass
            # elif refer_policy == "same-origin":
            #     splits = referrer.split("/", 3)
            #     top_host = splits[2]
            #     if ":" in top_host:
            #         new_host = top_host.split(":", 1)                    
            #         if self.host == new_host:
            #             body += f"referer: {referrer}\r\n"
            # else:
            #     body += f"referer: {referrer}\r\n"
                
            #we don't want it to have weird transfer or content encoding, if it does then break
            #also good for debugging, as it fails here we know why it failed
            assert "transfer-encoding" not in response_headers
            assert "content-encoding" not in response_headers
            
            # status = int(status)
            
            # if status == 404:
            #     raise FileNotFoundError("File not found:", self.path)
            
            # if 300 <= status and status < 400:
            #     redirect_url = response_headers["location"]
            #     if redirect_url.startswith("/"):
            #         redirect_url = f"{self.scheme}://{self.host}{redirect_url}"
            #     redirect_limit += 1
            #     return URL(redirect_url).request(redirect_limit = redirect_limit + 1)
                  
            
            # if "cache-control" in response_headers:
            #     if "no-store" not in response_headers["cache-control"].lower():
            #         max_age = int(response_headers["cache-control"].split("max-age=")[1])
            #         #print("TIME AT CACHE:", time.time(), "TIME FOR EXPIRY:", max_age + time.time())
            #         URL.cache[self.full_url] = (body, max_age + time.time())

            s.close()        
            return response_headers, body
    
    def __repr__(self):
        fragment_part = "" if self.fragment == None else ", fragment=" + self.fragment
        return "URL(scheme={}, host={}, port={}, path={!r}{})".format(
            self.scheme, self.host, self.port, self.path, fragment_part)
    
class RedirectLoopError(Exception):
    "Infinite redirect loop avoided"
    