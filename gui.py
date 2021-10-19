import os

import PySimpleGUI as sg
from project import search
from PIL import Image
import io

sg.change_look_and_feel('Material2')

searchLayout = [
    [sg.Image('./joogle.png', size=(760, 300))],
    [sg.Input(key='-query-')],
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

while True:  # The Event Loop
    event, values = window.read()
    print(event, values)
    if event == sg.WIN_CLOSED or event == 'Exit':
        break

    query = values['-query-']
    if event == 'Search':
        temp = print
        print = sg.Print
        search_results = search(query).values()
        print = temp
        for item in search_results:
            print("item", item)
            results.append(item)
        print(results)

        print(results)
        window[f'-search-layout-'].update(visible=False)
        window[f'-results-layout-'].update(visible=True)
        print(query)
        # Update the "output" text element to be the value of "input" element
        window['-output-'].update(values['-query-'])
        # window['-results-'].update(values[results])
        window.refresh()
    elif event == 'Back':
        window[f'-search-layout-'].update(visible=True)
        window[f'-results-layout-'].update(visible=False)

window.close()
