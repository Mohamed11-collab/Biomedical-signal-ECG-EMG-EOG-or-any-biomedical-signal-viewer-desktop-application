import PySimpleGUI as sg
import matplotlib.pyplot as plt
import neurokit2 as nk
import pandas as pd
import matplotlib.animation as anim
from matplotlib.backends._backend_tk import Toolbar, NavigationToolbar2Tk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg


class Toolbar(NavigationToolbar2Tk):
    # only display the buttons we need
    toolitems = [t for t in NavigationToolbar2Tk.toolitems if
                 t[0] in ('Home', 'Pan', 'Zoom', 'Save')]

    def init(self, *args, **kwargs):
        super(Toolbar, self).init(*args, **kwargs)


def draw_figure(canvas, figure, canvas_toolbar=None):
    figure_canvas_agg = FigureCanvasTkAgg(figure, canvas)
    figure_canvas_agg.draw_idle()
    if canvas_toolbar is not None:
        toolbar = Toolbar(figure_canvas_agg, canvas_toolbar)
        toolbar.update()
    figure_canvas_agg.get_tk_widget().pack(side='top', fill='both', expand=1)
    return figure_canvas_agg


def main():
    # define the form layout
    sg.SetOptions(background_color='#0e0a4e',
                  text_color="#0e0a4e",
                  text_element_background_color='#ffffff',
                  element_background_color='#0e0a4e',
                  button_color=('white', '#0e0a4e'))

    layout = [[sg.Text('Signal Viewer', size=(40, 1), justification='center', font='Helvetica 20')],
              [sg.Text('Press Spacebar to Pause'), sg.Text('Press ← to Move Backward'),
               sg.Text('Press → to Move Forward'), sg.Text('DELETE For Switch Sig')],
              [sg.Canvas(key='controls_cv', pad=((250, 0), 3))],
              [sg.Canvas(size=(640, 380), key='-CANVAS-')],
              [sg.Text('Please Choose The Signal You Want', size=(58, 1), justification='center', font='Helvetica 14')],
              [sg.Button('ECG', pad=((215, 0), 3)), sg.Button('EMG'), sg.Button('RSP'), sg.Button('READ FILE')],
              [sg.Button('Exit', size=(5, 1), pad=((280, 0), 3), font='Helvetica 14')]]

    # create the form and show it without the plot
    window = sg.Window('Signal Viewer', layout, finalize=True)
    canvas_elem = window['-CANVAS-']
    canvas = canvas_elem.TKCanvas
    fig, axis = plt.subplots(nrows=2)

    fig_agg = draw_figure(canvas, fig, window.FindElement('controls_cv').TKCanvas)

    def spectrogram(wavedata):
        axis[0].clear()
        axis[0].specgram(wavedata, NFFT=64, Fs=256, noverlap=32)
        axis[0].set_ylabel('Frequency (Hertz)')

    def wave_form(wavedata):
        x, y = [], []
        plt.grid(True)

        def update_time():
            t = 0
            t_axis = len(wavedata)
            while t < t_axis and t >= 0:
                t += ani.direction
                yield t

        def animate(frame):
            start, end = frame / 2, frame + 0.5
            x.append(wavedata[frame])
            plt.cla()
            plt.ylim([wavedata.min(), wavedata.max()])
            axis[1].plot(x)
            axis[1].set_xlabel('Samples')
            axis[1].set_ylabel('Voltage (mv)')
            plt.grid()
            plt.tight_layout()
            axis[1].set_xlim(start, end)

        def on_press(event1):
            if event1.key.isspace():
                if ani.running:
                    ani.event_source.stop()
                    ani.running ^= True
                else:
                    ani.event_source.start()
                    ani.running = True
            elif event1.key == 'delete':
                ani._stop()
            elif event1.key == 'left':
                ani.direction = -1
            elif event1.key == 'right':
                ani.direction = +1
            if event1.key in ['left', 'right']:
                t = ani.frame_seq.__next__()
                animate(t)

        fig.canvas.mpl_connect('key_press_event', on_press)

        ani = anim.FuncAnimation(plt.gcf(), animate, frames=update_time(), interval=5, repeat=True)
        ani.running = True
        ani.direction = +1
        fig_agg.draw_idle()

    while True:
        event, values = window.read(timeout=10)
        if event in ('Exit', sg.WIN_CLOSED):
            exit(69)
        elif event in 'ECG':
            wavedata = nk.ecg_simulate(duration=10, noise=0.01, heart_rate=100)
            wave_form(wavedata)
            spectrogram(wavedata)
        elif event in 'EMG':
            wavedata = nk.emg_simulate(duration=10, sampling_rate=300, burst_number=4)
            wave_form(wavedata)
            spectrogram(wavedata)
        elif event in 'RSP':
            wavedata = nk.rsp_simulate(duration=30, sampling_rate=50, noise=0.01)
            wave_form(wavedata)
            spectrogram(wavedata)
        elif event == "READ FILE":
            filename = sg.popup_get_file('filename to open', no_window=True, file_types=(("CSV Files", "*.csv"),))
            wavedata = pd.read_csv(filename)
            wavedata = wavedata.iloc[:, 0]
            wave_form(wavedata)
            spectrogram(wavedata)
    window.close()


if __name__ == '_main_':
    main()
