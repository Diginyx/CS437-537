import PySimpleGUI as sg

tasks = ["something", "something2", "something3"]

array = [("Bacon Meaty", ("Bacon ipsum dolor amet ham tenderloin rump ribeye, drumstick.", "Rump chuck turkey venison "
                                                                                           "burgdoggen boudin ham "
                                                                                           "meatball.\n")) for i in
         range(5)]
# + "\n" +
sg.change_look_and_feel('Material2')
layout = [
    [sg.Image('joogle.png', size=(760, 300))],
    [[[sg.Text(item[0], justification='left', text_color='blue')],
      [sg.Text(" " + item[1][0] + "\n " + item[1][1], pad=(0, 0)) if item[1][1] else sg.Text(item[1][0], pad=(0, 0))]]
     for item in array],
]
window = sg.Window('Playground', layout, resizable=True)
while True:  # Event Loop
    event, values = window.Read()
    if event == "add_save":
        tasks.append(values['todo_item'])
        window.FindElement('items').Update(values=tasks)
        window.FindElement('add_save').Update("Add")
    elif event == "Delete":
        tasks.remove(values["items"][0])
        window.FindElement('items').Update(values=tasks)
    elif event == "Edit":
        edit_val = values["items"][0]
        tasks.remove(values["items"][0])
        window.FindElement('items').Update(values=tasks)
        window.FindElement('todo_item').Update(value=edit_val)
        window.FindElement('add_save').Update("Save")
    elif event == None:
        break

window.Close()
