import views2 as view
import sys, os
def resource_path(relative_path):
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)
class begin:
    def __init__(self):
        start = view.showscreen()
        start.show()

if __name__ == "__main__":
    begin()