import os
import typing as ty

from kivy.uix.gridlayout import GridLayout
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.scrollview import ScrollView
from kivy.core.window import Window
from kivy.app import runTouchApp
from kivy.config import Config
import kivy

import reapy as rpr

import socket
REMOTE_SERVER = "8.8.8.8"

SECTION = 'rplayback'


def is_connected(hostname: str, port: int = 80):
    try:
        # see if we can resolve the host name -- tells us if there is
        # a DNS listening
        host = socket.gethostbyname(hostname)
        # connect to the host -- tells us if the host is actually
        # reachable
        s = socket.create_connection((host, port), 2)
        s.close()
        print(f'connected to "{hostname}:{port}"')
        return True
    except Exception as e:
        print(e)
    print(f'NOT connected to "{hostname}:{port}"')
    return False


class Item:

    def __init__(self, item: rpr.Item) -> None:
        self.item = item

    @property
    def name(self) -> str:
        return self.item.active_take.name

    @property
    def time(self) -> float:
        return self.item.position


def get_items_list(track_nr: int = 0) -> ty.List[Item]:
    try:
        rpr.Project()
    except (rpr.errors.DisabledDistAPIError, AttributeError):
        return []
    itemlist = []
    for item in filter(
        lambda item: item.track.index == track_nr,
        rpr.Project().items
    ):
        itemlist.append(Item(item))
    return itemlist


def get_layouts():
    layout = GridLayout(cols=1, spacing=10, size_hint_y=None)
    # layout.bind(minimum_height=layout.setter('height'))
    layout.bind(minimum_height=layout.setter('height'))
    root = ScrollView(size_hint=(1, 4))
    root.add_widget(layout)
    return root, layout


@rpr.inside_reaper()
def on_track(time: float, instance) -> None:
    # time = item.time
    rpr.Project().cursor_position = time
    # print(time, item.name)
    rpr.perform_action(1013)


def update_list(layout: GridLayout, itemlist: ty.List[Item]):
    layout.clear_widgets()
    try:
        rpr.Project()
    except (rpr.errors.DisabledDistAPIError, AttributeError):
        print('cannot connect')
        return
    with rpr.inside_reaper():
        for item in itemlist:
            btn = Button(
                text=item.name, size_hint_y=None, height=Window.height / 10
            )
            btn.bind(
                on_press=lambda instance, time=item.time:
                on_track(time, instance)
            )
            layout.add_widget(btn)


def update(_list, conn_text: TextInput, instance) -> None:
    # ping(conn_text.text)
    # is_connected(conn_text.text, 2307)
    try:
        conn = rpr.connect(conn_text.text)
        with rpr.inside_reaper():
            print(f'connected to {conn_text.text}')
    except (rpr.errors.DisabledDistAPIError, AttributeError):
        print('cannot connect to "{}"'.format(conn_text.text))
        # conn_text.background_color = (1, 0, 0)
        return
    # else:
    #     conn_text.background_color = (1, 1, 1)
    Config.set(SECTION, 'IP', conn_text.text)
    Config.write()
    print(f'SECTION, "IP" to {conn_text.text}')

    with rpr.inside_reaper():
        items_list = get_items_list()

        pr = rpr.Project()
        ts = pr.time_selection
        ts.start = 0
        ts.end = pr.length
        rpr.perform_action(40420)
        ts.end = 0

        for item in items_list:
            item_ = item.item
            pr.add_marker(item_.position + item_.length, name='!1016')

        print(items_list)
        update_list(_list, items_list)


def to_end() -> None:
    rpr.Project().cursor_position = rpr.Project().length + 1


def ping(hostname: str) -> None:

    # hostname = "google.com" #example
    response = os.system("ping -c 1 " + hostname)

    #and then check the response...
    if response == 0:
        print(hostname, 'is up!')
    else:
        print(hostname, 'is down!')


if __name__ == '__main__':
    is_connected('8.8.8.8')
    is_connected('ya.ru')
    Config.adddefaultsection(SECTION)
    Config.setdefault(SECTION, 'IP', "192.168.0.1")
    grid = GridLayout(cols=1, spacing=20)

    itemlist = get_items_list()
    print(*(item.name for item in itemlist), sep=' | ')
    scroll, layout = get_layouts()
    update_list(layout, itemlist)

    connection_grid = GridLayout(cols=2, spacing=10, size_hint_y=.5)
    conn_text = TextInput(text=Config.get(SECTION, 'IP'))
    ping("8.8.8.8")
    ping(conn_text.text)
    upd_btn = Button(text='update')
    upd_btn.bind(on_press=lambda instance: update(layout, conn_text, instance))
    connection_grid.add_widget(conn_text)
    connection_grid.add_widget(upd_btn)
    grid.add_widget(connection_grid)

    grid.add_widget(scroll)

    transport_grid = GridLayout(cols=4, spacing=10, size_hint_y=.5)
    play_btn = Button(text='play|rec')
    play_btn.background_color = (1, 0, 0)
    play_btn.bind(on_press=lambda instance: rpr.perform_action(1013))
    transport_grid.add_widget(play_btn)
    pause_btn = Button(text='pause')
    pause_btn.bind(on_press=lambda instance: rpr.perform_action(1008))
    pause_btn.background_color = (1, 1, 0)
    transport_grid.add_widget(pause_btn)
    stop_btn = Button(text='stop')
    stop_btn.bind(on_press=lambda instance: rpr.perform_action(1016))
    transport_grid.add_widget(stop_btn)
    end_btn = Button(text='to end')
    end_btn.bind(on_press=lambda instance: to_end())
    transport_grid.add_widget(end_btn)

    grid.add_widget(transport_grid)

    runTouchApp(grid)
