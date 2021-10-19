import os

import PySimpleGUI as sg
from project import search, output_to_file
from PIL import Image
import io

sg.change_look_and_feel('Material1')


searchLayout = [
    [sg.Image('./joogle.png', size=(760, 300))],
    [sg.Input(key='-query-', background_color="white", text_color="black")],
    [sg.Button('Search', bind_return_key=True), sg.Exit()]
]


results = []
resultsLayout = [
    [sg.Image('./joogle.png', size=(760, 300))],
    [sg.Text('You searched for: '), sg.Text(size=(15, 1), key='-output-')],
    [[[sg.Text(item[0], justification='left', text_color='blue')], [sg.Text(" " + item[1][0] + "\n " + item[1][1], pad=(0, 0)) if item[1][1] else sg.Text(item[1][0], pad=(0, 0))]] for item in results],
    [sg.Button('Back')]
]

layouts = [[sg.Column(searchLayout, key='-search-layout-'), sg.Column(resultsLayout, visible=False, key='-results'
                                                                                                        '-layout-')]]

window = sg.Window('Joogle', layouts, size=(1366, 768), resizable=True, element_justification='c',
                   return_keyboard_events=True, finalize=True)

second_open = False
second_window = None

while True:  # The Event Loop
    current_window = window
    if second_open:
        current_window = second_window

    event, values = current_window.Read()
    if event == sg.WIN_CLOSED or event == 'Exit':
        break

    if event == 'Search':
        query = values['-query-']
        search_results = search(query)
        print(search_results['results'])
        resultsLayout = [
            [sg.Image('joogle.png', size=(760, 300))],
            [[[sg.Text(item[1], text_color='blue', key='-TEXT-')],
              [sg.Text(" " + item[2][0] + "\n " + item[2][1], pad=(0, 0)) if item[2][1] else sg.Text(
                  item[2][0],
                  pad=(0, 0))]]
             for item in search_results['results']],
            [sg.Text("Query Suggestions")],
            [[sg.Text(suggestion[0])] for suggestion in search_results['query_suggestions']],
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
                os.startfile(output_to_file(res))
window.close()

