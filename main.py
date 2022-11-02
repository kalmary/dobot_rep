#from serial.tools import list_ports
import sys
import pandas as pd
import csv
import DobotArm as Dbt
import DobotDllType as dType
import numpy as np
import keyboard
from alive_progress import alive_bar
import time
# from voltage import volt
import threading
import PySimpleGUI as sg
import matplotlib.pyplot as plt
from matplotlib import cm
from matplotlib.ticker import LinearLocator

import board
import busio
import adafruit_ads1x15.ads1015 as ADS
from adafruit_ads1x15.analog_in import AnalogIn

def home():
    homey_max = 160.
    homex_min, homex_max = 180., 274.
    h_max, h_min = 50., -60.
    homeX, homeY, homeZ = homex_min, 0., h_max
    return homeX, homeY, homeZ, homey_max, homex_min, homex_max, h_max, h_min


def dim_list(start, stop, resolution):
    
    return np.arange(start, stop+resolution, resolution)
            
def ctrl_bot():
    homeX, homeY, homeZ, _, _, _, _, _ = home()
    ctrlBot = Dbt.DoBotArm(homeX, homeY, homeZ)

    return ctrlBot

def move_arm(b_div, a_div, h_div, side_div, ctrlBot, chan):
    n=len(a_div) * len(b_div)
    k=0
    
    
    
    volt = np.zeros((len(a_div), len(side_div)))
   
    side_div.tolist()
    
    layout = [
        [sg.Text('Processing... Please wait', expand_x=True, justification = 'center')],
        [sg.ProgressBar(max_value = n, orientation = 'h', size = (50, 15), key = '-prog-')],
        [sg.Text(f'Scanning point {k} of {n}', expand_x = True, key = '-progt-')],
        #[sg.EasyProgressMeter('Processing... Please wait', 0, n)],
        
        [sg.Text('', expand_x = True), sg.Button('STOP', key = '-stop-', button_color = 'red'), sg.Text('', expand_x = True)]
        ]

    i, j = 0, 0
#     print("Processing... Please wait")
    ctrlBot.moveArmXYZ(b_div[0], a_div[0], h_div[1])
    

    window = sg.Window('Progress', layout)
    #with alive_bar(n, dual_line=True, title='Total progress') as bar:

   
    for i in range(0, len(a_div)):
            #bar.text = f'-> Line: {i} of {len(a_div)}, please wait...'
        ctrlBot.moveArmXYZ(b_div[j], a_div[i], h_div[1])
        for j in range(0, len(b_div)):
            event, values = window.read(timeout = 1)
            
            ctrlBot.moveArmXYZ(b_div[j], a_div[i], h_div[0])
        
            #volt[i][j] = i
            #volt[i][j] = k
            volt[i][j] = chan.voltage
            
            if event == '-stop-':
                window.close()
                ctrlBot.moveArmXYZ(b_div[j], a_div[i], h_div[1])
                ctrlBot.dobotDisconnect()
                sys.exit()
            
            if event == sg.WIN_CLOSED:
                sys.exit()
            
            window['-progt-'].update(f'Scanning point {k+1} of {n}')    
            window['-prog-'].UpdateBar(k+1)
            #[sg.EasyProgressMeter('Processing... Please wait', k+1, n)]
            k+=1
        j = j - len(b_div)
        ctrlBot.moveArmXYZ(b_div[j], a_div[i], h_div[1])
        
        
      
    window.close()
    return volt
        


def connect_gui():
    sg.theme=('DarkTeal9')
    button_size = (5,3)
    sg.set_options(font = 'Franklin 15')
    padding = (5, 10)
    layout = [
        [sg.Button('Connect', expand_x='True', key = '-connect-', pad = padding), sg.Button('Quit', button_color = 'red' ,expand_x='True', key = '-quit-', pad = padding)],
         #[sg.Multiline('', key='-info-', background_color = 'white', font = 10, size = (40, 20),
          #             autoscroll=True)]
        [sg.Multiline('', key='-info-', background_color = 'white', font = 10, size = (30, 5),
                       autoscroll=True, reroute_stdout=True, reroute_stderr=True)]
        ]
    
    window=sg.Window('Connect', layout, finalize = True)
    print('Hello!')
    
    while True:
        event, values = window.read()
        
        if event == sg.WIN_CLOSED:
            break
        if event == '-connect-':
            api, ctrlBot, chan = connect()
            #window.close()
            what2do_GUI(api, ctrlBot, chan)
            break
        if event == '-quit-':
            break
    window.close()
    
    
def connect():

    ctrlBot=ctrl_bot()
    time.sleep(26)
    chan = voltage()
    return dType.load(), ctrlBot, chan

def what2do_GUI(api, ctrlBot, chan):
    
    homeX, homeY, homeZ, homey_max, homex_min, homex_max, h_max, h_min = home()
    
    a_max = 2 * homey_max
    b_max = homex_max - homex_min
    
    
    sg.theme=('random')
    button_size = (10,2)
    sg.set_options(font = 'Franklin 15')
    padding = (5, 5)
    layout = [
        [sg.Button('Scan with dimensions', size = button_size, key = '-scan-', pad = padding)],
        [sg.Button('Scan of the point', size = button_size, key = '-point-', pad = padding)],
        [sg.Button('Quit', button_color= 'red', size = button_size, key = '-quit-', pad = padding)]
        ]
    
    window=sg.Window('What2do', layout)
    
    while True:
        try:
            event, values = window.read()
            if event == sg.WIN_CLOSED:
                break
        
            if event == '-scan-':
                scan_gui(a_max, b_max, h_max, ctrlBot, homex_min, homeX, homeY, homeZ, chan)
        
            if event == '-point-':
                point_gui(ctrlBot, h_max, homeX, homeY, homeZ, chan)
            
            if event == '-quit-':
                break
            
        except TypeError:
            pass
            
    window.close()
            
def scan_gui(a_max, b_max, h_max, ctrlBot, homex_min, homeX, homeY, homeZ, chan):
    dim = [None] * 3
    
    res_values=np.around(np.arange(0.1, 5.1, 0.1), decimals = 2).tolist()
    
    button_size = (5, 2)
    pad_size = (10, 3)
    layout = [
        [sg.Text('Dimensions')],
        [sg.Input(f'Enter dimension a (width, a_max={a_max}) [mm]', key = '-a-', pad= pad_size, enable_events = True)],
        [sg.Input(f'Enter dimension b (length, b_max={b_max}) [mm]', key = '-b-', pad= pad_size, enable_events = True)],
        [sg.Input(f'Enter dimension h (height, h_max={h_max}) [mm]', key = '-h-', pad= pad_size, enable_events = True)],
        [sg.Text('Resolution:'), sg.Combo(res_values, default_value = f'{res_values[4]}', pad = pad_size, size = (5, 3), key='-res-')],
        [sg.Button('Start' ,key = '-start-'), sg.Button('Back', key = '-back-', pad= pad_size), sg.Button('Quit' , button_color='red', key = '-quit-', pad= pad_size)] 
        ]
    
    window=sg.Window('Scanner App', layout)
    
    while True:
        
        
        event, values = window.read()
        #print(values)
        if event == sg.WIN_CLOSED:
            break
        
        elif event == '-quit-':
            sys.exit()
            break

        elif event == '-back-':
            break

        input_value_a = values['-a-']
        input_value_b = values['-b-']
        input_value_h = values['-h-']
        
        
        if (input_value_a.isnumeric() == False or float(input_value_a) > a_max)  and event == '-a-':
            window['-a-'].update(f'Enter proper value of a (a_max = {a_max})', text_color = 'red')
            
        if (input_value_b.isnumeric() == False or float(input_value_b) > b_max) and event == '-b-':
            window['-b-'].update(f'Enter proper value of b (b_max = {b_max})', text_color = 'red')
            
        if (input_value_h.isnumeric() == False or float(input_value_h) > h_max+20) and event == '-h-':
            window['-h-'].update(f'Enter proper value of h (h_max = {h_max+20})', text_color = 'red')
        
        
        
        if input_value_a.isnumeric() == True and float(input_value_a) <= a_max and event == '-a-':
            window['-a-'].update(text_color = 'black')
            dim[0]=float(input_value_a)
            
        if input_value_b.isnumeric() == True and float(input_value_b) <= b_max and event == '-b-':
            window['-b-'].update(text_color = 'black')
            dim[1]=float(input_value_b)
            
        if input_value_h.isnumeric() == True and float(input_value_h) <= h_max+20 and event == '-h-':
            window['-h-'].update(text_color = 'black')
            dim[2]=float(input_value_h)        
        
        
        if input_value_a.isnumeric() == True and input_value_b.isnumeric() == True and input_value_h.isnumeric() == True and event == '-start-':
            res = float(values['-res-'])
            #print(dim, res)
            #return dim, res  
#         elif event == '-a-':
#             window['-a-'].update(f'')
          
            a_div, b_div, h_div = scan(dim, res, ctrlBot, homex_min, homeX, homeY, homeZ, chan)
            
            choose_plot_gui(a_div, side_div, res, volt)
            break
        
    window.close()
    
            
            
def done_gui(switch):
    if switch == 0:
        layout = [
            [sg.Text('Place the point under area indicated by arm', key = '-info-')],
             [sg.Button('Done', key = '-done-'), sg.Button('Quit', key = '-quit-')]
            ]
    elif switch == 1:
        layout = [
            [sg.Text('Point indicated by arm is the closer edge of plate surface.', key = '-info-')],
            [sg.Text('Put the examined sample symmetrically', key = '-info-')],
             [sg.Button('Done', key = '-done-'), sg.Button('Quit', key = '-quit-')]
            ]
        
    window = sg.Window('Scanner App', layout)
    
    while True:
        
        event, values = window.read()
        
        
        if event == sg.WIN_CLOSED:
            sys.exit()
        
        
        if event == '-quit-':
            sys.exit()
            
        if event == '-done-':
            break
            
    window.close()

def point_gui(ctrlBot, h_max, homeX, homeY, homeZ, chan):
    
    button_size = (5, 2)
    pad_size = (10, 3)
    res_values=np.around(np.arange(0.1, 5.1, 0.1), decimals = 2).tolist()
    
    layout = [
        [sg.Text('Height'), sg.Input(f'Enter h (height, h_max={h_max+20}) [mm]', key = '-h-', pad= pad_size, enable_events = True)],
        [sg.Text('Resolution:'), sg.Combo(res_values, default_value = f'{res_values[4]}', pad = pad_size, size = (5, 3), key='-res-')],
        [sg.Button('Start' ,key = '-start-'), sg.Button('Back', key = '-back-', pad= pad_size), sg.Button('Quit' , button_color='red', key = '-quit-', pad= pad_size)],
        #[sg.Text('Put the point under area indicated by arm: ', key = '-info-', text_color = 'white', visible = False), sg.Button('Done', key = '-done-', visible = False)]
        ]
    
    window =sg.Window('Point scan', layout)
   
    while True:
        
        event, values = window.read()
        
        
        if event == sg.WIN_CLOSED:
            break
        
        if event == '-quit-':
            sys.exit()
            break

        if event == '-back-':
            window.close()
            break
        
        input_value_h = values['-h-']
        
            
        if (input_value_h.isnumeric() == False or float(input_value_h) > h_max+20 or float(input_value_h)<0)  and event == '-h-':
            window['-h-'].update(f'Enter proper value of h (h_max = {h_max+20})', text_color = 'red')
            
        
        if input_value_h.isnumeric() == True and 0 < float(input_value_h) <= h_max+20 and event == '-h-':
            window['-h-'].update(text_color = 'black')
            #window['-info-'].update(visibile = True)
                
#         if event == '-start-':
#            
        if input_value_h.isnumeric() == True and (0 < float(input_value_h) <= h_max+20) and event == '-start-':
          
            h=float(input_value_h)
            res = float(values['-res-'])
            
            h=h-100
            h_div=[h+70, h+80]
            
    
            
            
            
            
                
            a_div, b_div, volt = point_move(h, h_div, res, ctrlBot, h_max, homeX, homeY, homeZ, chan)
            choose_plot_gui(a_div, b_div, res, volt)
                
            break
        
                
    window.close()
        
    
def point_move (h, h_div, res, ctrlBot, h_max, homeX, homeY, homeZ, chan):
    #ctrlBot.moveHome()
    
  
    area_side=16
    
    a_div=dim_list(-area_side/2,area_side/2, res)
    b_div=dim_list(homeX-area_side/2, homeX+area_side/2, res)
    side_div = get_side(b_div, res)
    #with ctrlBot.safe_stop():
    #print('Processing. Please wait...')
    ctrlBot.moveArmXYZ(b_div[int(len(b_div)/2)], a_div[int(len(a_div)/2)], h_div[1])
    
    for i in range(0, 3):
                ctrlBot.pickToggle(h_div[0])
                ctrlBot.pickToggle(h_div[1])
    done_gui(0)
    
    volt = move_arm(b_div, a_div, h_div, side_div, ctrlBot, chan)
    ctrlBot.moveHome()
    
    print(f"-----SCANNING SUCCESS-----")

    return a_div, b_div, volt

def scan(dim, res, ctrlBot, homex_min, homeX, homeY, homeZ, chan):
    
    resolution=res
    
    a_div=dim_list(-dim[0]/2, dim[0]/2, resolution) #kierunek y (dluzsza tablica)
    b_div=dim_list(homex_min, homex_min+dim[1], resolution) #krotsza tablica
    side_div = get_side(b_div, res)
    dim[2]=dim[2]-100
    h_div = [dim[2] + 70, dim[2] + 80]  # offset
    
    ctrlBot.moveHome()
    
    for i in range(0, 3):
        ctrlBot.pickToggle(h_div[0])
        ctrlBot.pickToggle(h_div[1])
            
    done_gui(1) 
 
    volt = move_arm(b_div, a_div, h_div, side_div, ctrlBot, chan)
    ctrlBot.moveHome()
    print(f"-----SCANNING SUCCESS-----")
    
    choose_plot_gui(a_div, side_div, res, volt)
    
    
    

    


def voltage():
    
    # Create the I2C bus
    i2c = busio.I2C(board.SCL, board.SDA)

    # Create the ADC object using the I2C bus
    ads = ADS.ADS1015(i2c)
    
    #chan = AnalogIn(ads, ADS.P0, ADS.P1)
    chan = AnalogIn(ads, ADS.P0)
    
    return chan


def choose_plot_gui(a_div, side_div, res, volt):
    padding = (5, 5)
    themes = [
        'Grey',
        'Grey reversed',
        'Heatmap',
        'Heatmap reversed',
        'Magma',
        'Magma reversed'
        ]
    pad_size = (10, 3)
    layout = [
        [sg.Checkbox('2D', default = False, key='-2d-', enable_events = True),
         sg.Checkbox('3D', default = False, key='-3d-', enable_events = True),
         sg.Text('Theme:'), sg.Push(),
         sg.Combo(themes, default_value = f'{themes[1]}', pad = pad_size, key='-combo-')], #line 1
        [sg.Button('Generate plot', key = '-start-')], #line 2
        [sg.InputText(key = 'File to save', default_text = 'file_name', enable_events = True),
         sg.InputText(key = 'Save As', do_not_clear = False, enable_events = True, visible = False),
         sg.FileSaveAs(initial_folder = '/home/michalsiniarski/programming/dobot_wyniki')], #line 3
        [sg.Button('Back', key = '-back-', pad= padding),
         sg.Button('Quit' , button_color='red', key = '-quit-', pad= padding)] #line 4
        ]
    
    window=sg.Window('What2do', layout)
    
    while True:

        event, values = window.read()
        if event == sg.WIN_CLOSED:
            break
        
        if event == '-back-':
            break
        
        if event == '-quit-':
            sys.exit()
        
        if event == 'Save As':
            filename = values['Save As']
            if filename:
                window['File to save'].update(value = filename)
                df = pd.DataFrame(volt, columns = side_div, index = a_div)
                df.to_csv(values['Save As'], float_format = '%4f', sep = ';')
        
        if values['-2d-'] == True and event == '-2d-':
            window['-3d-'].update(value = False)
            window['-2d-'].update(value = True)
            
        if event == '-start-' and values['-2d-'] == True:
            if values['-combo-'] == 'Grey':
                graph2d(a_div, side_div, res, volt, 'Greys')

            if values['-combo-'] == 'Grey reversed':
                graph2d(a_div, side_div, res, volt, 'Greys_r')
                    
            if values['-combo-'] == 'Heatmap':
                graph2d(a_div, side_div, res, volt, 'coolwarm')
                    
            if values['-combo-'] == 'Heatmap reversed':
                graph2d(a_div, side_div, res, volt, 'coolwarm_r')
                    
            if values['-combo-'] == 'Magma':
                graph2d(a_div, side_div, res, volt, 'magma')
                
            if values['-combo-'] == 'Magma reversed':
                graph2d(a_div, side_div, res, volt, 'magma_r')
                    

                    
        if values['-3d-'] == True and event == '-3d-':
            window['-2d-'].update(value = False)
            window['-3d-'].update(value = True)
            
        if event == '-start-' and values['-3d-'] == True:
            if values['-combo-'] == 'Grey':
                graph3d(a_div, side_div, res, volt, 'Greys')

            if values['-combo-'] == 'Grey reversed':
                graph3d(a_div, side_div, res, volt, 'Greys_r')
                    
            if values['-combo-'] == 'Heatmap':
                graph3d(a_div, side_div, res, volt, 'coolwarm')
                    
            if values['-combo-'] == 'Heatmap reversed':
                graph3d(a_div, side_div, res, volt, 'coolwarm_r')
                    
            if values['-combo-'] == 'Magma':
                graph3d(a_div, side_div, res, volt, 'magma')
            
            if values['-combo-'] == 'Magma reversed':
                graph3d(a_div, side_div, res, volt, 'magma_r')
            
    window.close()


def get_side(b_div, res):
    side = b_div[len(b_div) - 1] - b_div[0]
    side_div = np.arange(0, side + res, res)
   
    return side_div


def graph2d(a_div, side_div, res, volt, theme):
    
    
    Z = volt

    X, Y = np.meshgrid(side_div, a_div)
    
    axis = plt.gca()
    map = axis.pcolor(X, Y, Z, cmap = cm.get_cmap(theme))
    
    axis.set_aspect('equal')
    cb = plt.colorbar(mappable = map)    
    cb.set_label('voltage [V]', labelpad=2)
    
    
    plt.xlabel('b [mm]')
    plt.ylabel('a [mm]')
    plt.show()
    
def graph3d(a_div, side_div, res, volt, theme):
    
    fig, ax = plt.subplots(subplot_kw={"projection": "3d"})
    
    X, Y = np.meshgrid(side_div, a_div)
    z = volt
    surf = ax.plot_surface(X, Y, z, cmap=cm.get_cmap(theme), linewidth=0, antialiased=False)
    #ax.set_zlim(-3, 3)
    ax.set_title("Results 3D plot")
    ax.zaxis.set_major_locator(LinearLocator(10))
    # A StrMethodFormatter is used automatically
    ax.zaxis.set_major_formatter('{x:.02f}')
    # Add a color bar which maps values to colors.
    
    cb = fig.colorbar(surf, shrink=2.5, aspect=5)
    cb.set_label('voltage [V]')
    
    ax.set_xlabel('b [mm]')
    ax.set_ylabel('a [mm]')
    
    plt.show()

def main():
    connect_gui()
    
if __name__ == "__main__":
    main()