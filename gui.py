import PySimpleGUI as sg
from project import search, output_to_file
import subprocess

sg.change_look_and_feel('Material1')

searchLayout = [
    [sg.Image('./joogle.png', size=(760, 300))],
    [sg.Input(key='-query-', background_color="white", text_color="black")],
    [sg.Button('Search', bind_return_key=True), sg.Exit()]
]

#


window = sg.Window('Search', searchLayout, resizable=True, element_justification='c',
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
        search_results, query_suggestions = search(query)
        print("search results:", search_results)
        print("query_suggestions:", query_suggestions)
        if len(search_results) > 1:
            second_window = sg.Window('Results', [
                [sg.Image('joogle_results.png', size=(760, 300), pad=(0, 0))],
                [[[sg.Text(item[1], text_color='blue', key=(item[0]), enable_events=True, metadata=(item[0]))],
                  [sg.Text(" " + item[2][0] + "\n " + item[2][1], size=(70, 2), pad=(0, 0))]] for item in
                 search_results],
                [sg.Text("Query Suggestions")],
                [sg.Text(suggestion[0]) for suggestion in query_suggestions],
                [sg.Button('Back')]
            ], finalize=True, resizable=True)

        elif len(search_results) < 1:
            second_window = sg.Window('Results', [
                [sg.Image('joogle_results.png', size=(760, 300), pad=(0, 0))],
                [sg.Text('No Results were found for the query:' + query)],
                [sg.Text("Query Suggestions")],
                [sg.Text(suggestion[0]) for suggestion in query_suggestions],
                [sg.Button('Back')]
            ], finalize=True, resizable=True)

        while True:
            second_open = True
            event, values = second_window.Read()
            if event == sg.WIN_CLOSED or event == 'Exit':
                break
            elif event == "Back":
                second_open = False
                second_window.close()
                break
            for item in search_results:
                if event != item[0]:
                    continue

                filename = output_to_file(item[0])
                file = open(filename)
                print(file.readline())
                print(item[0])
                # subprocess.Popen(["notepad", filename])
                # subprocess.run(["notepad", filename])
                subprocess.call(['open', '-a', 'TextEdit', filename])
                break

window.close()
