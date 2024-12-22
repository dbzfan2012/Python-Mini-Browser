class Rect:
  def __init__(self, left, top, right, bottom):
        self.left = left
        self.top = top
        self.right = right
        self.bottom = bottom

  def containsPoint(self, x, y):
      return x >= self.left and x < self.right \
          and y >= self.top and y < self.bottom
          
  def __repr__(self):
    return "Rect({}, {}, {}, {})".format(self.left, self.top, self.right, self.bottom)


class DrawText:
    def __init__(self, x1, y1, text, font, color):
        self.rect = Rect(x1, y1, 
                         x1 + font.measure(text), y1 + font.metrics("linespace"))
        self.text = text
        self.font = font
        self.color = color
        
    def execute(self, scroll, canvas):
        canvas.create_text(
            self.rect.left, self.rect.top - scroll,
            text = self.text,
            font=self.font,
            anchor = "nw",
            fill = self.color
        )
        
    def __repr__(self):
        return "DrawText(top={} left={} bottom={} text={} font={})".format(self.rect.top, self.rect.left, self.rect.bottom, self.text, self.font)
        
class DrawRect:
    def __init__(self, rect, color, width):
        self.rect = rect
        self.color = color
        self.width = width

    def execute(self, scroll, canvas):
        canvas.create_rectangle(
            self.rect.left, self.rect.top - scroll,
            self.rect.right, self.rect.bottom - scroll,
            width=self.width,
            fill=self.color)
        
    def __repr__(self):
        return "DrawRect(top={} left={} bottom={} right={} color={})".format(self.rect.top, self.rect.left, self.rect.bottom, self.rect.right, self.color)

class DrawOutline:
  def __init__(self, rect, color, thickness):
        self.rect = rect
        self.color = color
        self.thickness = thickness

  def execute(self, scroll, canvas):
      canvas.create_rectangle(
          self.rect.left, self.rect.top - scroll,
          self.rect.right, self.rect.bottom - scroll,
          width=self.thickness,
          outline=self.color)
    
  def __repr__(self):
    return "DrawOutline({}, {}, {}, {}, color={}, thickness={})".format(
      self.left, self.top, self.right, self.bottom,
      self.color, self.thickness)
    
class DrawLine:
  def __init__(self, x1, y1, x2, y2, color, thickness):
    self.rect = Rect(x1, y1, x2, y2)
    self.color = color
    self.thickness = thickness
    
  def execute(self, scroll, canvas):
    canvas.create_line(
      self.rect.left, self.rect.top - scroll,
      self.rect.right, self.rect.bottom - scroll,
      fill = self.color, width = self.thickness)
    
  def __repr__(self):
    return "DrawLine({}, {}, {}, {}, color={}, thickness={})".format(
      self.rect.left, self.rect.top, self.rect.right, self.rect.bottom,
      self.color, self.thickness)