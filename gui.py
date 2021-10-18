import PySimpleGUI as sg
from project import search

sg.theme('DarkBlue')  # Keep things interesting for your users

searchLayout = [
    [sg.Input(key='-query-')],
    [sg.Button('Search'), sg.Exit()]
]

results = []
resultsLayout = [
    [sg.Text('You searched for: '), sg.Text(size=(15, 1), key='-output-')],
    *[[sg.Text(str(item[0]), "\n", str(item[1][0]))] for item in results],
    [sg.Button('Back')]
]

layouts = [[sg.Column(searchLayout, key='-search-layout-'), sg.Column(resultsLayout, visible=False, key='-results'
                                                                                                        '-layout-')]]

window = sg.Window('Joogle', layouts, size=(1368, 722), element_justification='c')

while True:  # The Event Loop
    event, values = window.read()
    print(event, values)
    if event == sg.WIN_CLOSED or event == 'Exit':
        break

    query = values['-query-']
    if query:
        for item in search(query):
            results.append(item)
        resultsLayout = [
            [sg.Text('You searched for: '), sg.Text(size=(15, 1), key='-output-')],
            *[[sg.Text(item[0] + "\n" + item[1][0] + " " + item[1][1] if not None else "")] for item in results],
            [sg.Button('Back')]
        ]
        print(results)
        window[f'-search-layout-'].update(visible=False)
        window[f'-results-layout-'].update(visible=True)
    print(query)

    if event == 'Search':
        # Update the "output" text element to be the value of "input" element
        window['-output-'].update(values['-query-'])
    elif event == 'Back':
        window[f'-search-layout-'].update(visible=True)
        window[f'-results-layout-'].update(visible=False)

window.close()
