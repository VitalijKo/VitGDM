import asyncio
import eel
import gd
import pymem
import pygame
import win32api
import win32con
import win32gui
import threading
import shutil
import base64
import os
import signal
import json
import time
from pygame.locals import *
from ctypes import windll, Structure, c_long, byref
from PIL import Image
from client import Client
from openclientport import open_client_port

os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = 'hide'


class RECT(Structure):
    _fields_ = [
        ('left', c_long),
        ('top', c_long),
        ('right', c_long),
        ('bottom', c_long),
    ]

    def width(self):
        return self.right - self.left

    def height(self):
        return self.bottom - self.top


def get_addr(offsets):
    addr = mem.read_int(base)

    for i in offsets:
        addr = mem.read_int(addr + i)

    return addr


def get_addr_string(offsets, acc=0):
    if len(offsets) == 1:
        addr = mem.read_int(base_acc if acc else base)
        addr = mem.read_string(addr + offsets[0])

        return addr

    else:
        addr = mem.read_int(base_acc if acc else base)

        for i in offsets[:-1]:
            addr = mem.read_int(addr + i)

        addr = mem.read_string(addr + offsets[-1])

        return addr


def get_addr_float(offsets):
    if len(offsets) == 1:
        addr = mem.read_int(base)
        addr = mem.read_float(addr + offsets[0])

        return addr

    else:
        addr = mem.read_int(base)

        for i in offsets[:-1]:
            addr = mem.read_int(addr + i)

        addr = mem.read_float(addr + offsets[-1])

        return addr


def get_addr_uchar(offsets):
    if len(offsets) == 1:
        addr = mem.read_int(base)
        addr = mem.read_uchar(addr + offsets[0])

        return addr

    else:
        addr = mem.read_int(base)

        for i in offsets[:-1]:
            addr = mem.read_int(addr + i)

        addr = mem.read_uchar(addr + offsets[-1])

        return addr


def calculate_icon(is_ship, is_ball, is_ufo, is_wave, is_robot, is_spider):
    if is_ship == 1:
        icon = 'Ship'

    elif is_ball == 1:
        icon = 'Ball'

    elif is_ufo == 1:
        icon = 'Ufo'

    elif is_wave == 1:
        icon = 'Wave'

    elif is_robot == 1:
        icon = 'Robot'

    elif is_spider == 1:
        icon = 'Spider'

    else:
        icon = 'Cube'

    return icon


def get_player_1_info():
    try:
        percent = get_addr_string(game_offsets['percent'])
        is_reverse = get_addr_uchar(game_offsets['is_reverse'])
        x = get_addr_float(player_1_offsets['x'])
        y = get_addr_float(player_1_offsets['y'])
        rotation = get_addr_float(player_1_offsets['rotation'])
        is_dead = get_addr_uchar(game_offsets['is_dead'])
        is_ship = get_addr(player_1_offsets['is_ship'])
        is_ball = get_addr(player_1_offsets['is_ball'])
        is_ufo = get_addr(player_1_offsets['is_ufo'])
        is_wave = get_addr(player_1_offsets['is_wave'])
        is_robot = get_addr(player_1_offsets['is_robot'])
        is_spider = get_addr(player_1_offsets['is_spider'])
        icon = calculate_icon(is_ship, is_ball, is_ufo, is_wave, is_robot, is_spider)
        gravity = get_addr_uchar(player_1_offsets['gravity'])
        size = get_addr_uchar(player_1_offsets['size'])

        player_1_info = {
            'percent': percent,
            'is_reverse': is_reverse,
            'x': x,
            'y': y,
            'rotation': rotation,
            'is_dead': is_dead,
            'is_ship': is_ship,
            'is_ball': is_ball,
            'is_ufo': is_ufo,
            'is_wave': is_wave,
            'is_robot': is_robot,
            'is_spider': is_spider,
            'icon': icon,
            'gravity': gravity,
            'size': size,
        }

        return player_1_info
    except:
        return 1


def get_player_2_info():
    try:
        x = get_addr_float(player_2_offsets['x'])
        y = get_addr_float(player_2_offsets['y'])
        rotation = get_addr_float(player_2_offsets['rotation'])
        is_ship = get_addr(player_2_offsets['is_ship'])
        is_ball = get_addr(player_2_offsets['is_ball'])
        is_ufo = get_addr(player_2_offsets['is_ufo'])
        is_wave = get_addr(player_2_offsets['is_wave'])
        is_robot = get_addr(player_2_offsets['is_robot'])
        is_spider = get_addr(player_2_offsets['is_spider'])
        icon = calculate_icon(is_ship, is_ball, is_ufo, is_wave, is_robot, is_spider)
        gravity = get_addr_uchar(player_2_offsets['gravity'])
        size = get_addr_uchar(player_2_offsets['size'])

        player_2_info = {
            'x': x,
            'y': y,
            'rotation': rotation,
            'is_ship': is_ship,
            'is_ball': is_ball,
            'is_ufo': is_ufo,
            'is_wave': is_wave,
            'is_robot': is_robot,
            'is_spider': is_spider,
            'icon': icon,
            'gravity': gravity,
            'size': size,
        }

        return player_2_info
    except:
        return 1


def calculate_x(window_width, is_reverse):
    if not is_reverse:
        x = window_width / 3

    else:
        x = window_width * (3 / 4)

    return x


def calculate_y(player_y, window_y, window_width, window_height, cam_y):
    player_y -= cam_y
    player_y += 10

    y_offset = (window_width - 1000) * 0.0016

    y = (window_y + window_height) - (player_y * (1.92 + y_offset))

    if y <= (window_y + 50):
        y = window_y + 75

    elif y >= (window_y + window_height - 75):
        y = window_y + window_height - 100

    return y


def calculate_connected_player_x(player_x, connected_player_x, player_screen_x, window_width):
    screen_x_offset = (window_width - 1000) * 0.0018

    x_offset = (player_x - connected_player_x) * (1.8 + screen_x_offset)

    connected_player_screen_x = player_screen_x + x_offset

    return connected_player_screen_x


def is_visible(player_x, connected_player_x):
    for i in range(int(player_x - 200), int(player_x + 345)):
        if int(connected_player_x) == i:
            return 1

    return 0


def window_callback(hwnd, _):
    window_name = win32gui.GetWindowText(hwnd)

    if window_name == 'Geometry Dash':
        global game_hwnd

        game_hwnd = hwnd

    elif window_name == 'VitGDM Multiplayer':
        global app_hwnd

        app_hwnd = hwnd


def find_hwnds():
    global app_hwnd

    win32gui.EnumWindows(window_callback, None)

    if not app_hwnd:
        app_hwnd = None


def get_window_coords():
    window_coords = {
        'x': 0,
        'y': 0,
        'w': 0,
        'h': 0,
    }

    rect = win32gui.GetWindowRect(game_hwnd)
    x = rect[0]
    y = rect[1]
    w = rect[2] - x
    h = rect[3] - y

    if x >= 0:
        window_coords = {
            'x': x,
            'y': y,
            'w': w,
            'h': h,
        }

    return window_coords


def format_payload(percent, is_dead, p1_icon, p2_icon, p1_x, p1_y, p2_x, p2_y, wx, wy, ww, wh, cam_y,
                   p1_rotation, p2_rotation, is_reverse, p1_gravity, p2_gravity, p1_size, p2_size):
    payload = \
        str(percent) \
        + ',' + str(is_dead) \
        + ',' + str(p1_icon) \
        + ',' + str(p2_icon) \
        + ',' + str(p1_x) \
        + ',' + str(p1_y) \
        + ',' + str(p2_x) \
        + ',' + str(p2_y) \
        + ',' + str(wx) \
        + ',' + str(wy) \
        + ',' + str(ww) \
        + ',' + str(wh) \
        + ',' + str(cam_y) \
        + ',' + str(p1_rotation) \
        + ',' + str(p2_rotation) \
        + ',' + str(is_reverse) \
        + ',' + str(p1_gravity) \
        + ',' + str(p2_gravity) \
        + ',' + str(p1_size) \
        + ',' + str(p2_size)

    return payload


def parse_payload(player_name, payload):
    payload = payload.split(',')
    percent = payload[0]
    is_dead = payload[1]
    p1_icon = payload[2]
    p2_icon = payload[3]
    p1_x = payload[4]
    p1_y = payload[5]
    p2_x = payload[6]
    p2_y = payload[7]
    wx = payload[8]
    wy = payload[9]
    ww = payload[10]
    wh = payload[11]
    cam_y = payload[12]
    p1_rotation = payload[13]
    p2_rotation = payload[14]
    is_reverse = payload[15]
    p1_gravity = payload[16]
    p2_gravity = payload[17]
    p1_size = payload[18]
    p2_size = payload[19]

    return player_name, percent, is_dead, p1_icon, p2_icon, p1_x, p1_y, p2_x, p2_y, wx, wy, ww, wh, cam_y, \
        p1_rotation, p2_rotation, is_reverse, p1_gravity, p2_gravity, p1_size, p2_size


def write_info(is_playing, level_name='N/A', level_difficulty='UNRATED', level_id='N/A', capacity='?'):
    if not is_playing:
        info = {
            'rooms': rooms
        }

    else:
        players = connected_players_info.copy()

        for player in list(players):
            try:
                players[player][2] = connected_players_icons_base64[player][icon_number(players[player][2])]
            except:
                players[player][0] = 'Downloading icons...'
                players[player][2] = ''

        info = {
            'level_name': level_name,
            'level_difficulty': level_difficulty,
            'level_id': level_id,
            'players': players,
            'capacity': capacity
        }

    eel.set_interface(info, is_playing)


def write_connected_players_info(name, percent, is_dead, p1_icon, p2_icon, p1_x, p1_y, p2_x, p2_y, wx, wy, ww, wh,
                                 cam_y, p1_rotation, p2_rotation, is_reverse, p1_gravity, p2_gravity, p1_size, p2_size):
    global connected_players_info

    connected_players_info[name] = [percent, is_dead, p1_icon, p2_icon, p1_x, p1_y, p2_x, p2_y, wx, wy, ww,
                                    wh, cam_y, p1_rotation, p2_rotation, is_reverse, p1_gravity, p2_gravity, p1_size,
                                    p2_size]

    try:
        download_icons(name)
    except:
        pass


def player_icon_path(name, icon):
    icons_path = root_images + name + '/'

    path_to_icon = icons_path + 'cube.png'

    if icon == 'cube':
        path_to_icon = icons_path + 'cube.png'

    elif icon == 'ship':
        path_to_icon = icons_path + 'ship.png'

    elif icon == 'ball':
        path_to_icon = icons_path + 'ball.png'

    elif icon == 'ufo':
        path_to_icon = icons_path + 'ufo.png'

    elif icon == 'wave':
        path_to_icon = icons_path + 'wave.png'

    elif icon == 'robot':
        path_to_icon = icons_path + 'robot.png'

    elif icon == 'spider':
        path_to_icon = icons_path + 'spider.png'

    icon_image = pygame.image.load(path_to_icon).convert_alpha()

    with open(path_to_icon, 'rb') as image_file:
        base64_icon_image = 'data:image/png;base64,' + base64.b64encode(image_file.read()).decode('utf-8')

    return icon_image, base64_icon_image


async def get_level_info(level_id):
    level = await gdc.get_level(level_id, get_data=False, use_client=True)

    level_name = level.name
    level_difficulty = \
        str(level.difficulty).replace('Difficulty.', '').replace('_', ' ')

    return level_name, level_difficulty


async def get_user_info(username):
    user = await gdc.search_user(username)

    user = {
        'cube': user.cube_id,
        'ship': user.ship_id,
        'ball': user.ball_id,
        'ufo': user.ufo_id,
        'wave': user.wave_id,
        'robot': user.robot_id,
        'spider': user.spider_id,
        'col1': user.color_1_id,
        'col2': user.color_2_id,
        'glow': int(user.glow)
    }

    return user


def get_icon(name, form, icon, col1, col2, glow):
    icon_image = Image.open(f'premade_icons/{"icon" if form == "cube" else form}_{icon}.png').convert('RGBA')
    icon_image.save(f'{root_images}{name}/{form}.png', 'PNG')


def download_icons(name):
    global downloading
    global connected_players_icons
    global connected_players_icons_base64

    downloading = ''

    if not os.path.exists(root_images + name):
        os.mkdir(root_images + name)

        forms = ['cube', 'ship', 'ball', 'ufo', 'wave', 'robot', 'spider']

        downloading = name

        icons_images = [0] * 7
        icons_images_base64 = [0] * 7

        user = asyncio.run(get_user_info(name))

        for i in range(len(forms)):
            form = forms[i]

            get_icon(name, form, user[form], user['col1'], user['col2'], user['glow'])

            icons_images[i], icons_images_base64[i] = player_icon_path(name, form)

        connected_players_icons[name] = icons_images
        connected_players_icons_base64[name] = icons_images_base64

        downloading = ''

    else:
        if name not in connected_players_icons:
            forms = ['cube', 'ship', 'ball', 'ufo', 'wave', 'robot', 'spider']

            icons_images = [0] * 7
            icons_images_base64 = [0] * 7

            for i in range(len(forms)):
                form = forms[i]
                icons_images[i], icons_images_base64[i] = player_icon_path(name, form)

            connected_players_icons[name] = icons_images
            connected_players_icons_base64[name] = icons_images_base64


def flip(surface):
    flipped_surface = pygame.transform.flip(surface, False, True)

    return flipped_surface


def rotate(surface, angle):
    rotated_surface = pygame.transform.rotozoom(surface, -angle, 1)

    return rotated_surface


def icon_number(icon):
    if icon == 'Cube':
        return 0

    elif icon == 'Ship':
        return 1

    elif icon == 'Ball':
        return 2

    elif icon == 'Ufo':
        return 3

    elif icon == 'Wave':
        return 4

    elif icon == 'Robot':
        return 5

    elif icon == 'Spider':
        return 6


def get_icon_size(icon_number, size_offset, player_size):
    size = (50 + size_offset, 50 + size_offset)

    if icon_number == 0:
        size = (50 + size_offset, 50 + size_offset)

    elif icon_number == 1:
        size = (85 + size_offset, 40 + size_offset)

    elif icon_number == 2:
        size = (55 + size_offset, 55 + size_offset)

    elif icon_number == 3:
        size = (60 + size_offset, 50 + size_offset)

    elif icon_number == 4:
        size = (60 + size_offset, 45 + size_offset)

    elif icon_number == 5:
        size = (55 + size_offset, 50 + size_offset)

    elif icon_number == 6:
        size = (60 + size_offset, 50 + size_offset)

    if player_size:
        size = (size[0] // 2.5, size[1] // 2.5)

    return size


def draw_players(p1_x, p1_screen_x, p2_screen_x, is_reverse, window_width):
    for name in connected_players_info:
        info = connected_players_info[name]
        icon_images = connected_players_icons[name]

        info[4] = float(info[4])
        info[5] = float(info[5])
        info[7] = float(info[7])
        info[8] = int(info[8])
        info[9] = int(info[9])
        info[10] = int(info[10])
        info[11] = int(info[11])
        info[12] = float(info[12])
        info[13] = float(info[13])
        info[14] = float(info[14])
        info[15] = int(info[15])
        info[16] = int(info[16])
        info[17] = int(info[17])
        info[18] = int(info[18])
        info[19] = int(info[19])

        visibility = is_visible(p1_x, info[4])

        if not visibility:
            return 0

        if is_reverse == 1:
            p1_x = int(calculate_connected_player_x(p1_x, info[4] + 100, p1_screen_x, info[10]))

        else:
            p1_x = int(calculate_connected_player_x(p1_x, info[4], p1_screen_x, info[10]))

        p1_y = int(calculate_y(info[5], info[9], info[10], info[11], info[12]))

        name_text = font.render(name, False, (255, 255, 255))

        dual = False

        if p2_screen_x != -1:
            p2_x = p1_x
            p2_y = int(calculate_y(info[7], info[9], info[10], info[11], info[12]))

            dual = True

        p1_icon_number = icon_number(info[2])

        p1_rotation = info[13]
        p2_rotation = info[14]

        p1_size = info[18]

        size_offset = int(((window_width - 1000) * 0.06))

        p1_icon_size = get_icon_size(p1_icon_number, size_offset, p1_size)

        p1_icon = pygame.transform.scale(icon_images[p1_icon_number], p1_icon_size)

        screen.blit(name_text, (info[8] + p1_x + p1_icon_size[0] // 3, p1_y - 35))

        if not info[16]:
            if info[15] == 1:
                p1_rotation += 180

                screen.blit((rotate(flip(p1_icon), p1_rotation)), (info[8] + p1_x, p1_y))

            else:
                screen.blit(rotate(p1_icon, p1_rotation), (info[8] + p1_x, p1_y))
        else:
            if info[15] == 1:
                p1_rotation += 180

                screen.blit((rotate(flip(p1_icon), p1_rotation)), (info[8] + p1_x, p1_y))

            else:
                screen.blit((rotate(flip(p1_icon), p1_rotation)), (info[8] + p1_x, p1_y))

        if dual:
            p2_icon_number = icon_number(info[3])

            p2_size = info[19]

            p2_icon_size = get_icon_size(p2_icon_number, size_offset, p2_size)

            p2_icon = pygame.transform.scale(icon_images[p2_icon_number], p2_icon_size)

            if not info[17]:
                if info[15] == 1:
                    p1_rotation += 180

                    screen.blit((rotate(flip(p2_icon), p2_rotation)), (info[8] + p2_x, p2_y))

                else:
                    screen.blit(rotate(p2_icon, p2_rotation), (info[8] + p2_x, p2_y))

            else:
                if info[15] == 1:
                    p1_rotation += 180

                    screen.blit((rotate(flip(p2_icon), p2_rotation)), (info[8] + p2_x, p2_y))

                else:
                    screen.blit((rotate(flip(p2_icon), p2_rotation)), (info[8] + p2_x, p2_y))


def check_playing():
    is_playing = True

    try:
        get_addr_string(game_offsets['percent'])
    except:
        is_playing = False

    return is_playing


def connect(ip):
    global client

    try:
        client = Client(ip, 7575, 7575, 7575)
    except:
        eel.call_alert(
            'error',
            'Error',
            'Server is off! '
            'Try restarting the multiplayer. '
            'If the problem repeats, please come back later, '
            'or choose a different server.',
            1
        )


def list_to_dict(lst):
    res_dct = {lst[i]: lst[i + 1] for i in range(0, len(lst), 2)}

    return res_dct


def load_settings():
    default_server_ip = 'vib.fvds.ru'
    default_fps = 60
    default_icons = False

    if not os.path.exists(settings_path):
        with open(settings_path, 'w') as settings_file:
            settings_file.write(
                f'SERVER: {default_server_ip}\n'
                f'FPS: {default_fps}\n'
                f'ICONS: {default_icons}'
            )

    with open(settings_path, 'r') as settings_file:
        settings = settings_file.readlines()

    try:
        for setting in list(settings):
            settings.remove(setting)

            setting = setting.replace('\n', '').split(': ')

            try:
                setting[1] = int(setting[1])
            except:
                pass

            setting[1] = setting[1] == 'True'

            settings.append(setting[0])
            settings.append(setting[1])

        settings = list_to_dict(settings)
    except:
        os.remove(settings_path)

        with open(settings_path, 'w') as settings_file:
            settings_file.write(
                f'SERVER: {default_server_ip}\n'
                f'FPS: {default_fps}\n'
                f'ICONS: {default_icons}'
            )

        settings = {
            'SERVER': default_server_ip,
            'FPS': default_fps,
            'ICONS': default_icons
        }

    return settings


def init_account_icons():
    global player_icon_base64

    download_icons(acc_name)

    player_icon = f'{root_images}/{acc_name}/cube.png'

    with open(player_icon, 'rb') as image_file:
        player_icon_base64 = 'data:image/png;base64,' + base64.b64encode(image_file.read()).decode('utf-8')

    eel.set_account_info(acc_name, player_icon_base64)


def make_on_top(window):
    rc = RECT()
    windll.user32.GetWindowRect(window, byref(rc))
    windll.user32.SetWindowPos(window, -1, rc.left, rc.top, 0, 0, 0x0001)


def prepare(init=True):
    global acc_name
    global settings
    global FPS
    global display_icons
    global screen
    global font
    global display_hwnd
    global clock

    if init:
        time.sleep(2)

        acc_name = get_addr_string(global_offsets['acc_name'], True)

        if not os.path.exists(root):
            os.mkdir(root)

        if os.path.exists(root_images):
            shutil.rmtree(root_images)

        os.mkdir(root_images)

        find_hwnds()

        pygame.init()
        pygame.font.init()

        font = pygame.font.SysFont('Bahnschrift', 22)
        clock = pygame.time.Clock()

        flags = FULLSCREEN | DOUBLEBUF | NOFRAME

        screen = pygame.display.set_mode((win32api.GetSystemMetrics(0), win32api.GetSystemMetrics(1)), flags)

        display_hwnd = pygame.display.get_wm_info()['window']

        pygame.event.set_allowed(None)
        pygame.display.set_caption('VitGDM Display')
        icon = pygame.image.load('ui/favicon.ico')
        pygame.display.set_icon(icon)

        init_icons = threading.Thread(target=init_account_icons)
        init_icons.start()

        make_on_top(display_hwnd)

        win32gui.SetWindowLong(
            display_hwnd,
            win32con.GWL_EXSTYLE,
            win32gui.GetWindowLong(display_hwnd, win32con.GWL_EXSTYLE) | win32con.WS_EX_LAYERED
        )

        win32gui.SetLayeredWindowAttributes(display_hwnd, win32api.RGB(255, 0, 128), 0, win32con.LWA_COLORKEY)

    else:
        disconnect(True)

    try:
        settings = load_settings()
        server = settings['SERVER']
        FPS = settings['FPS']
        display_icons = settings['ICONS']
    except:
        os.remove(settings_path)
        settings = load_settings()
        server = settings['SERVER']
        FPS = settings['FPS']
        display_icons = settings['ICONS']

    connect(server)

    if not init:
        if client:
            eel.call_alert(
                'success',
                'Success!'
            )

        eel.set_account_info(acc_name, player_icon_base64)


@eel.expose()
def download_update():
    eel.call_alert(
        'error',
        'Error',
        'Some error occured.'
    )


@eel.expose()
def check_update():
    update = False

    if update:
        eel.call_alert(
            'confirm',
            'Info',
            'New version available!',
            0,
            True
        )

    else:
        eel.call_alert(
            'success',
            'Latest version',
            'You have the latest version of multiplayer.'
        )


@eel.expose()
def open_ports():
    try:
        open_client_port(7575)

        eel.call_alert(
            'success',
            'Success',
            'The ports have been successfully opened!'
        )
    except Exception as e:
        eel.call_alert(
            'error',
            'Error',
            str(e)
        )


@eel.expose()
def change_settings(data):
    with open(settings_path, 'w') as settings_file:
        for key in data:
            if key == 'FPS':
                if int(data[key]) > 360:
                    data[key] = 360

                elif int(data[key]) < 30:
                    data[key] = 30

            settings_file.write(f'{key}: {data[key]}\n')

    prepare(False)


@eel.expose()
def get_settings():
    while True:
        try:
            return settings
        except:
            time.sleep(1)


def disconnect(close_connection=False):
    global client

    try:
        if client is not None and client.room_id is not None:
            data = {'name': acc_name, 'message': 'leave'}

            client.send(data)
            client.leave_room()
    except:
        pass

    if close_connection:
        try:
            client.server_listener.stop()
            client.sock_tcp.close()
        except:
            pass

        client = None


def check_app_open():
    while app_hwnd is False:
        time.sleep(1)

    if not app_hwnd or not win32gui.GetWindowText(app_hwnd):
        disconnect()
        os.kill(os.getpid(), signal.SIGTERM)

    time.sleep(1)

    eel.set_account_info(acc_name, player_icon_base64)


def check_events(events):
    for e in events:
        if e.type == pygame.QUIT:
            disconnect()
            os.kill(os.getpid(), signal.SIGTERM)


def close_callback(_, __):
    check_open = threading.Thread(target=check_app_open)
    check_open.start()


def application():
    eel.init('ui')

    try:
        eel.start(
            'app.html',
            disable_cache=True,
            close_callback=close_callback,
            cmdline_args=[
                '--incognito',
                '--no-experiments',
                '--window-size=700,800',
                '--window-position=700,220'
            ]
         )
    except:
        os.kill(os.getpid(), signal.SIGTERM)


client = None
display_hwnd = None
game_hwnd = None
app_hwnd = False
player_icon_base64 = None
prev_level_id = None
prev_player_x = None
interface_update_countdown = 50
window_check_countdown = 100
root = 'C://VitGDM/'
root_images = root + 'images/'
settings_path = root + 'settings.dat'
downloading = ''
connected_players_info = {}
connected_players_icons = {}
connected_players_icons_base64 = {}

global_offsets = {
    'acc_name': [0x108],
}

game_offsets = {
    'percent': [0x164, 0x3C0, 0x12C],
    'is_dead': [0x164, 0x39C],
    'level_id': [0x2A0],
    'cam_y': [0x164, 0x490],
    'is_reverse': [0x164, 0x47C],
}

player_1_offsets = {
    'x': [0x164, 0x224, 0x4E8, 0xB4, 0x67C],
    'y': [0x164, 0x224, 0x680],
    'rotation': [0x164, 0x224, 0x020],
    'is_ship': [0x164, 0x224, 0x638],
    'is_ball': [0x164, 0x224, 0x63A],
    'is_ufo': [0x164, 0x224, 0x639],
    'is_wave': [0x164, 0x224, 0x63B],
    'is_robot': [0x164, 0x224, 0x63C],
    'is_spider': [0x164, 0x224, 0x63D],
    'gravity': [0x164, 0x224, 0x63E],
    'size': [0x164, 0x224, 0x644],
}

player_2_offsets = {
    'x': [0x164, 0x228, 0x4E8, 0xB4, 0x67C],
    'y': [0x164, 0x228, 0x680],
    'rotation': [0x164, 0x228, 0x020],
    'is_ship': [0x164, 0x228, 0x638],
    'is_ball': [0x164, 0x228, 0x63A],
    'is_ufo': [0x164, 0x228, 0x639],
    'is_wave': [0x164, 0x228, 0x63B],
    'is_robot': [0x164, 0x228, 0x63C],
    'is_spider': [0x164, 0x228, 0x63D],
    'gravity': [0x164, 0x228, 0x63E],
    'size': [0x164, 0x228, 0x644],
}

app = threading.Thread(target=application, daemon=True)
app.start()

try:
    mem = pymem.Pymem('GeometryDash.exe')
    gdc = gd.Client()

    base = pymem.process.module_from_name(mem.process_handle, 'GeometryDash.exe').lpBaseOfDll + 0x3222D0
    base_acc = pymem.process.module_from_name(mem.process_handle, 'GeometryDash.exe').lpBaseOfDll + 0x3222D8

    prepare()
except pymem.exception.ProcessNotFound:
    eel.call_alert(
        'error',
        'Error',
        'Geometry Dash is not opened!',
        2
    )

    os.kill(os.getpid(), signal.SIGTERM)
except:
    eel.call_alert(
        'error',
        'Error',
        'Service temporarily unavailable. '
        'The problem is not with the server. '
        'Please come back later.',
        2
    )

    os.kill(os.getpid(), signal.SIGTERM)

while True:
    try:
        events = pygame.event.get()
        check_events(events)

        screen.fill((255, 0, 128))

        if client and player_icon_base64:
            is_playing = check_playing()
            level_id = get_addr(game_offsets['level_id'])

            if window_check_countdown >= 100:
                window_coords = get_window_coords()

                if win32gui.GetWindowText(win32gui.GetForegroundWindow()) != 'VitGDM Display':
                    make_on_top(display_hwnd)

                window_check_countdown = 0

            if not is_playing:
                if client.room_id is not None:
                    disconnect()

                    connected_players_info = {}
                    connected_players_icons = {}
                    connected_players_icons_base64 = {}
                    client.room_id = None

                try:
                    rooms = client.get_rooms()
                except:
                    pass

                if interface_update_countdown >= 50:
                    write_info(False)

                    interface_update_countdown = 0

            if is_playing:
                if level_id != prev_level_id:
                    try:
                        capacity = '?'

                        level_name, level_difficulty = asyncio.run(get_level_info(level_id))
                    except gd.errors.MissingAccess:
                        eel.call_alert(
                            'error',
                            'Error',
                            'Levels with N/A difficulty are not supported!'
                        )
                    except RuntimeError:
                        pass
                    except Exception as e:
                        if client.room_id is not None:
                            disconnect()

                        eel.call_alert(
                            'error',
                            'Error',
                            str(e)
                        )

                        connected_players_info = {}
                        connected_players_icons = {}
                        connected_players_icons_base64 = {}
                        client.room_id = None
                        level_name = 'N/A'
                        level_difficulty = 'UNRATED'

                prev_level_id = level_id

                if client.room_id is None:
                    joined = False

                    rooms = client.get_rooms()

                    for room in rooms:
                        if room['name'] == str(level_id):
                            client.join_room(room['id'])

                            joined = True

                    if not joined:
                        client.create_room(str(level_id), level_name, level_difficulty)

                if interface_update_countdown >= 50 and capacity == '?':
                    try:
                        rooms = client.get_rooms()

                        for room in rooms:
                            if client.room_id == room['id']:
                                capacity = rooms[0]['capacity']

                                break
                    except:
                        pass

                p1_info = get_player_1_info()
                p2_info = get_player_2_info()

                try:
                    p1_x = p1_info['x']
                    p1_y = p1_info['y']
                    p2_x = p2_info['x']
                    p2_y = p2_info['y']
                    wx = window_coords['x']
                    wy = window_coords['y']
                    ww = window_coords['w']
                    wh = window_coords['h']
                    is_reverse = p1_info['is_reverse']
                    p1_gravity = p1_info['gravity']
                    p2_gravity = p2_info['gravity']
                    p1_size = p1_info['size']
                    p2_size = p2_info['size']
                    p1_screen_x = int(calculate_x(ww, is_reverse))

                    if p2_x == p1_x:
                        p2_screen_x = p1_screen_x

                    else:
                        p2_screen_x = -1

                    cam_y = int(get_addr_float(game_offsets['cam_y']))
                    percent = p1_info['percent']
                    p1_icon = p1_info['icon']
                    p2_icon = p1_info['icon']
                    p1_rotation = p1_info['rotation']
                    p2_rotation = p2_info['rotation']
                    is_dead = p1_info['is_dead']
                except:
                    is_playing = False

                if interface_update_countdown >= 50:
                    write_info(True, level_name, level_difficulty, level_id, capacity)

                    interface_update_countdown = 0

                if client.room_id is not None:
                    try:
                        payload = format_payload(percent, is_dead, p1_icon, p2_icon, p1_x, p1_y, p2_x, p2_y,
                                                 wx, wy, ww, wh, cam_y, p1_rotation, p2_rotation, is_reverse,
                                                 p1_gravity, p2_gravity, p1_size, p2_size)

                        data = {'name': acc_name, 'message': payload}

                        client.send(data)
                    except:
                        pass

                    messages = client.get_messages()

                    for message in messages:
                        message = json.loads(message)
                        sender, message = message.popitem()
                        player_name = message['name']

                        if not player_icon_base64 or player_name == acc_name:
                            continue

                        if message['message'] == 'leave':
                            if player_name in connected_players_info:
                                connected_players_info.pop(player_name)
                                connected_players_icons.pop(player_name)
                                connected_players_icons_base64.pop(player_name)

                        else:
                            write_connected_players_info(*parse_payload(player_name, message['message']))

                    if connected_players_info:
                        if display_icons and p1_x != prev_player_x:
                            try:
                                prev_player_x = p1_x
                                
                                draw_players(p1_x, p1_screen_x, p2_screen_x, is_reverse, ww)
                            except:
                                pass


            interface_update_countdown += 1
            window_check_countdown += 1

        pygame.display.update()
        clock.tick(FPS)
    except AttributeError:
        time.sleep(1)
    except ConnectionRefusedError:
        eel.call_alert(
            'error',
            'Error',
            'Server is off! '
            'Try restarting the multiplayer. '
            'If the problem repeats, please come back later, '
            'or choose a different server.',
            1
        )
