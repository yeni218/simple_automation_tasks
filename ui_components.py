from pywinauto import Application

app = Application(backend="uia").connect(title='MainWindow')
# app.MainWindow.dump_tree() # useful to get child_window spec for just a copy-paste!

target = app.MainWindow.child_window(title='TARGET', control_type='Edit').wrapper_object()
# maybe try control_type='Text' depending on info from Inspect.exe

# when you found the control, just get the text
target.legacy_properties()['Value'] # .legacy_properties() returns a dict