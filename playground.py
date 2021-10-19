import PySimpleGUI as sg
import os

tasks = ["something", "something2", "something3", "something2", "something3"]

sg.change_look_and_feel('Material1')

searchLayout = [
    [sg.Image('./joogle.png', size=(760, 300))],
    [sg.Input(key='-query-', background_color="white", text_color="black")],
    [sg.Button('Search', bind_return_key=True), sg.Exit()]
]

second_open = False
window = sg.Window('Playground', searchLayout, resizable=True, element_justification='c', )
second_window = None
while True:  # Event Loop
    current_window = window
    if second_open:
        current_window = second_window

    event, values = current_window.Read()
    if event == sg.WIN_CLOSED or event == 'Exit':
        break

    if event == 'Search':
        resultsLayout = [
            [sg.Image('joogle.png', size=(760, 300))],
            [[[sg.Text(item[0], text_color='blue', key='-TEXT-')],
              [sg.Text(" " + item[1][0] + "\n " + item[1][1], key="test2", pad=(0, 0)) if item[1][1] else sg.Text(
                  item[1][0],
                  pad=(0, 0),
                  key="test3")]]
             for item in results],
            [sg.Text("Query Suggestions")],
            [[sg.Text(suggestion)] for suggestion in tasks],
            [sg.Button('Back')]
        ]
        while True:
            second_window = sg.Window('Results', resultsLayout, finalize=True)
            second_open = True
            event, values = second_window.Read()
            if event == "Back":
                second_open = False
                second_window.close()
                break
    elif event == '-TEXT-':
        os.startfile('project.py')

        # wiki_dataframe['title'][document]
        # wiki_dataframe['content'][document]
window.close()
