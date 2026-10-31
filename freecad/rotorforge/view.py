"""Open generated frames from the +Y nose instead of FreeCAD's rear isometric."""
import FreeCAD as App


def front_view_rotation():
    eye=App.Vector(1,1,1)
    right=App.Vector(0,0,1).cross(eye)
    up=eye.cross(right)
    return App.Rotation(right,up,eye,'ZXY')


def view_front():
    import FreeCADGui as Gui
    if Gui.activeDocument():
        view=Gui.activeDocument().activeView()
        view.setCameraOrientation(front_view_rotation().Q)
        view.fitAll()
