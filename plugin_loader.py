from wxglade_layout import *
import os
import re
# import time
import json
import subprocess
import threading
from itertools import cycle

EXTENSAO_VST2 = '.so'
EXTENSAO_VST2_WINE = '.dll'

EXTENSAO_FOLDER_VST3 = '.vst3'
EXTENSAO_VST3_WINE = '.vst3'


class Plugin(PluginFrame):

    def __init__(self, *args, **kwds):
        PluginFrame.__init__(self, *args, **kwds)

        dir = os.path.dirname(__file__)
        os.chdir(dir)  # altera o diretório atual para o do arquivo
        self.arch = self.combo_box_arch.GetStringSelection()
        self.repeat_retry_connection = 0
        self.audio_connections = 0
        self.vst2, self.vst3, self.vst2_dirs_list_config, self.vst3_dirs_list_config, self.lv2_names, self.lv2_uri = [], [], [], [], [], []
        self.load_vst, self.load_lv2 = '', ''
        self.vst2_dict, self.vst3_dict, self.lv2_dict = dict(), dict(), dict()
        self.midi_keyboard_substring, self.terminal, self.midi_keyboard, self.interface_substring = '', '', '',''
        self.config_json = dict()  # json file with the setup contents
        self.lsp_ports = []
        self.midi_input, self.midi_output, self.midi_in_hardware, self.midi_out_hardware = [], [], [], []
        self.audio_input, self.audio_output, self.audio_in_hardware, self.audio_out_hardware = [], [], [], []
        self.input_app, self.output_app, self.output_app_midi, self.input_app_midi = [], [], [], []
        self.added_terminal_options, self.app_names = [], []

        self.read_config()
        self.atualiza_listas()
        self.set_size()

    def set_size(self):
        '''Define o tamanho da janela de acordo com o ambiente de trabalho'''
        de = os.environ.get('DESKTOP_SESSION')
        if de == 'plasma': # kde
            self.SetSize((800, 530))
        else: # tested only with 'gnome':
            self.SetSize((850, 620))


    def read_config(self):
        with open('./.config', 'r') as config_file:
            self.config_json = json.load(config_file)
        self.load_setup_data()

    def load_setup_data(self):
        '''Load the config contents in the 'Setup' Tab'''
        self.vst2_dirs_list_config = self.config_json.get('vst2_dirs', '[]')
        self.load_config_vst2_listbox()

        self.vst3_dirs_list_config = self.config_json.get('vst3_dirs', '[]')
        self.load_config_vst3_listbox()

        self.midi_keyboard_substring = self.config_json.get('keyboard_substring', '')
        self.text_ctrl_keyboard_substring.SetValue(self.midi_keyboard_substring)

        self.terminal = self.config_json.get('terminal', '')
        if self.terminal:
            self.combo_box_terminal.SetValue(self.terminal)

        self.added_terminal_options = self.config_json.get('added_terminal_options', [])
        if self.added_terminal_options:
            for option in self.added_terminal_options:
                self.combo_box_terminal.Append(option)

        self.load_vst = self.config_json.get('load_vst', True)
        self.checkbox_load_vst.SetValue(self.load_vst)

        self.load_lv2 = self.config_json.get('load_lv2', True)
        self.checkbox_load_lv2.SetValue(self.load_lv2)

        self.repeat_retry_connection = self.config_json.get('connect_retry')
        self.combo_box_autoconnect_retry.SetValue(str(self.repeat_retry_connection))

        self.interface_substring = self.config_json.get('interface')
        self.text_ctrl_interface_substring.SetValue(self.interface_substring)

        self.audio_connections = self.config_json.get('audio_connections')
        self.combo_box_audio_connections.SetValue(str(self.audio_connections))

    def load_config_vst2_listbox(self):
        self.list_box_vst2_directories.Clear()
        for item in self.vst2_dirs_list_config:
            self.list_box_vst2_directories.Append(item)

    def load_config_vst3_listbox(self):
        self.list_box_vst3_directories.Clear()
        for item in self.vst3_dirs_list_config:
            self.list_box_vst3_directories.Append(item)

    def write_config(self):
        with open('.config', 'w') as file:
            json.dump(self.config_json, file, sort_keys=True, indent=4)

    def atualiza_listas(self):
        '''Load the vsts names in the listboxes'''
        self.list_box_vst_lv2.Clear()
        if self.load_vst: # if setup is set to load vst
            self.vst2_dict.clear()
            for folder2 in self.vst2_dirs_list_config:
                for foldername, subfolders, filenames in os.walk(folder2):
                    for filename in filenames:
                        if self.arch == 'native':
                            if filename.endswith(EXTENSAO_VST2):
                                key = filename[:-3] + ' - VST2'
                                if key not in self.vst2_dict:
                                    self.vst2_dict[key] = os.path.join(foldername, filename)
                        else:
                            if filename.endswith(EXTENSAO_VST2_WINE) and filename[:-4] not in self.vst2_dict:
                                key = filename[:-4] + ' - VST2'
                                if key not in self.vst2_dict:
                                    self.vst2_dict[key] = os.path.join(foldername, filename)

            for key in sorted(self.vst2_dict.keys()):
                if key:
                    self.list_box_vst_lv2.Append(key)

            self.vst3_dict.clear()
            for folder3 in self.vst3_dirs_list_config:
                for foldername, subfolders, filenames in os.walk(folder3):
                    if self.arch == 'native':
                        for subfolder in subfolders:
                            if subfolder.endswith(EXTENSAO_FOLDER_VST3):
                                key = subfolder[:-5] + ' - VST3'
                                if key not in self.vst3_dict:
                                    self.vst3_dict[key] = os.path.join(foldername, subfolder)
                    else:
                        for filename in filenames:
                            if filename.endswith(EXTENSAO_VST3_WINE) and self.arch != 'native':
                                key = filename[:-5] + ' - VST3'
                                if key not in self.vst3_dict:
                                    self.vst3_dict[key] = os.path.join(foldername, filename)
            for key in sorted(self.vst3_dict.keys()):
                if key:
                    self.list_box_vst_lv2.Append(key)

        if self.load_lv2: # if setup is set to load lv2
            if not self.lv2_dict:
                self.atualiza_listas_lv2()
            for key in sorted(self.lv2_dict.keys()):
                if key:
                    self.list_box_vst_lv2.Append(key)

    def get_lv2_names(self):
        '''recupera os nomes dos lv2'''
        lv2_plugins_name = subprocess.run(['lv2ls', '-n'], capture_output=True, text=True)
        # gera uma lista com os nomes
        self.lv2_names = lv2_plugins_name.stdout.split('\n')

    def get_lv2_uri(self):
        '''recupera os uri dos lv2'''
        lv2_plugins_uri = subprocess.run(['lv2ls'], capture_output=True, text=True)
        # gera uma lista com os uri
        self.lv2_uri = lv2_plugins_uri.stdout.split('\n')

    def atualiza_listas_lv2(self):
        '''recupera os lv2 usando threads para recuperar nome e uri concomitantemente'''
        if not self.lv2_uri:  #se vazio
            # Creating threads for each method
            thread1 = threading.Thread(target=self.get_lv2_names)
            thread2 = threading.Thread(target=self.get_lv2_uri)

            # Starting both threads
            thread1.start()
            thread2.start()

            # Waiting for both threads to finish
            thread1.join()
            thread2.join()

            print("Done...")

            self.lv2_dict = {self.lv2_names[i] + ' - LV2': self.lv2_uri[i] for i in range(len(self.lv2_names)) if (self.lv2_names[i] and self.lv2_names[i]!='(null)')}
            # print(self.lv2_dict)

    def listbox_vst_lv2_double_click(self, event):  # wxGlade: MyFrame.<event_handler>
        '''Recover the selected item in the Listbox and calls the method chama_rotina()'''
        choice_vst = self.list_box_vst_lv2.GetStringSelection()
        print(f'Running {choice_vst}')
        if ' - VST2' in choice_vst:
            # print(self.vst2_dict[choice_vst])
            if self.arch == 'native':
                extensao = EXTENSAO_VST2
            else:
                extensao = EXTENSAO_VST2_WINE

            if self.terminal != '-':
                # print(f"{self.terminal} -e carla-single {self.arch} vst2 '{self.vst2_dict[choice_vst]}' &")
                os.system(f"{self.terminal} -e carla-single {self.arch} vst2 '{self.vst2_dict[choice_vst]}' &")

            else:
                # os.system(f"carla-single {self.arch} vst2 '{choice_vst[:-7]}{extensao}' &")
                os.system(f"carla-single {self.arch} vst2 '{self.vst2_dict[choice_vst]}' &")

        elif ' - VST3' in choice_vst:
            if self.arch == 'native':
                extensao = EXTENSAO_FOLDER_VST3
            else:
                extensao = EXTENSAO_VST3_WINE
            # terminal_command = f'{self.terminal} -e '
            if self.terminal != '-':
                # os.system(f"{self.terminal} -e carla-single {self.arch} vst3 '{choice_vst[:-7]}{extensao}' &")
                os.system(f"{self.terminal} -e carla-single {self.arch} vst3 '{self.vst3_dict[choice_vst]}' &")

            else:
                os.system(f"carla-single {self.arch} vst3 '{self.vst3_dict[choice_vst]}' &")

        else:  #lv2
            prefix_console = ''
            if self.terminal != '-':
                prefix_console = self.terminal + ' -e '
            if not self.checkbox_jalv.GetValue():
                os.system(f'{prefix_console}carla-single native lv2 {self.lv2_dict[choice_vst]} &')
            else:
                os.system(
                    f'{prefix_console}jalv.gtk3 {self.lv2_dict[choice_vst]} &')  # recupera o comando do dicionário

        # self.recover_jack_names(self.repeat_retry_connection)

        if self.checkbox_autoconnect.GetValue():
            if 'yabridge' in choice_vst.lower() or (self.arch != 'native' and '- VST' in choice_vst):
                # time.sleep(3)
                wx.Sleep(4)
            else:
                # time.sleep(1)
                wx.Sleep(1)
            self.connect_jack()

        event.Skip()


    def combobox_change_arch(self, event):  # wxGlade: VstFrame.<event_handler>
        self.arch = self.combo_box_arch.GetStringSelection()
        # self.search_ctrl_1.SetValue('')
        self.atualiza_listas()
        self.vst_search()
        event.Skip()

    def clear_lists(self):
        lists = [self.midi_input, self.midi_output, self.midi_in_hardware, self.midi_out_hardware, self.audio_input,
                 self.audio_output, self.audio_in_hardware, self.audio_out_hardware, self.input_app, self.output_app,
                 self.output_app_midi, self.input_app_midi]

        for list in lists:
            list.clear()

    def recover_jack_names(self, event=None):
        '''Read jack ports e send it to a temp file'''
        app_name = ''
        choice_vst_lv2 = self.list_box_vst_lv2.GetStringSelection()
        if choice_vst_lv2:
            if '- VST' in choice_vst_lv2:
                app_name = choice_vst_lv2[:-7]
            else:  # lv2
                app_name = choice_vst_lv2[:-6]
        if not app_name:
            return
        selected_app = app_name.split('/')[-1].split()
        for app in selected_app:
            if app not in self.app_names:
                self.app_names.append(app)  # divide o nome para consulta por suas partes
                app_split_4 = app.split('/')[-1][:3]
                if app_split_4 not in self.app_names:
                    self.app_names.append(app_split_4)  # tenta recuperar a porta 4 primeiras letras do app
            # self.app_names.append(app.split('/')[-1][-4:])  # tenta recuperar a porta 4 últimas letras do app
        # print(self.app_names)


    def get_lsp_ports(self, repeat_retry=2):
        '''Generate list os jack ports'''
        self.clear_lists()
        os.system("jack_lsp -p >> lsp")
        with open('lsp', 'r') as ports:
            self.lsp_ports = ports.read()
            self.lsp_ports = re.sub(r'\n\tproperties: ', '|', self.lsp_ports).split('\n')
            # print(self.lsp_ports)
            for port in self.lsp_ports:
                if 'input,physical' in port.lower() and 'midi' in port.lower():
                    self.midi_in_hardware.append(port.split('|')[0])
                    continue
                elif 'output,physical' in port.lower() and 'midi' in port.lower():
                    self.midi_out_hardware.append(port.split('|')[0])
                    continue
                elif 'events-in' in port.lower():
                    self.midi_input.append(port.split('|')[0])
                    continue
                elif 'events-out' in port.lower():
                    self.midi_output.append(port.split('|')[0])
                    continue
                elif 'input,physical' in port.lower():
                    if not self.interface_substring or self.interface_substring.lower() in port.lower():
                        self.audio_in_hardware.append(port.split('|')[0])
                    continue
                elif 'output,physical' in port.lower():
                    if not self.interface_substring or self.interface_substring.lower() in port.lower():
                        self.audio_out_hardware.append(port.split('|')[0])
                    continue
                elif 'input' in port.lower():
                    self.audio_input.append(port.split('|')[0])
                    continue
                elif 'output' in port.lower() and 'monitor' not in port.lower():
                    self.audio_output.append(port.split('|')[0])
        os.remove('lsp')
        self.midi_keyboard = next((s for s in self.midi_out_hardware if self.midi_keyboard_substring in s), None)
        # print('midi_in_h', self.midi_in_hardware, '\n')
        # print('midi_out_h', self.midi_out_hardware, '\n')
        # print('midi_in', self.midi_input, '\n')
        # print('midi_out', self.midi_output, '\n')
        # print('audio_in_h', self.audio_in_hardware, '\n')
        # print('audio_out_h', self.audio_out_hardware, '\n')
        # print('audio_in', self.audio_input, '\n')
        # print('audio_out', self.audio_output, '\n')


        if repeat_retry and not self.audio_output:
            wx.Sleep(2)
            self.get_lsp_ports(repeat_retry - 1)

    def connect_jack(self, event=None):
        # if not self.audio_output:
        self.get_lsp_ports(self.repeat_retry_connection)
        self.recover_jack_names()
        # print(self.audio_connections)
        audio_app_in, audio_app_out, audio_in_map, audio_out_map = [], [], [], []
        for name_app in self.app_names:
            for input_audio in self.audio_input: # generates audio ports lists
                if name_app in input_audio and input_audio not in audio_app_in:
                    audio_app_in.append(input_audio)
            for output_audio in self.audio_output: # generates audio ports lists
                if name_app in output_audio and output_audio not in audio_app_out:
                    audio_app_out.append(output_audio)
            for midi_input in self.midi_input: # connect midi keyboard
                if name_app in midi_input:
                    os.system(f"jack_connect '{self.midi_keyboard}' '{midi_input}' &")

        if self.audio_connections: # if restricted the number os connections
            audio_in_hard_conn, audio_out_hard_conn = [], []
            for connection in range(self.audio_connections):
                audio_in_hard_conn.append(self.audio_in_hardware[connection])
                audio_out_hard_conn.append(self.audio_out_hardware[connection])

            audio_in_map = list(zip(audio_app_in, cycle(audio_out_hard_conn)))
            audio_out_map = list(zip(audio_app_out, cycle(audio_in_hard_conn)))

        else:
            audio_in_map = list(zip(audio_app_in, self.audio_out_hardware))
            audio_out_map = list(zip(audio_app_out, self.audio_in_hardware))

        # print(audio_app_in)
        # print(audio_app_out)
        # print(audio_in_map)
        # print(audio_out_map)

        for connections_in in audio_in_map:
            # print(connections_in)
            os.system(
                f"jack_connect '{connections_in[0]}' '{connections_in[1]}' &")  #conecta portas de entrada

        for connections_out in audio_out_map:
            # print(connections_out)
            os.system(
                f"jack_connect '{connections_out[0]}' '{connections_out[1]}' &")  #conecta portas de saída


    def vst_search(self, event=None):  # wxGlade: MyFrame.<event_handler>
        '''Filter the vst listboxes'''
        filter_string = self.search_ctrl_1.GetValue().lower()
        self.list_box_vst_lv2.Clear()
        if self.load_vst:
            for key in sorted(self.vst2_dict.keys()):
                if filter_string in key.lower():
                    self.list_box_vst_lv2.Append(key)
            for key in sorted(self.vst3_dict):
                if filter_string in key.lower():
                    self.list_box_vst_lv2.Append(key)

        if self.checkbox_load_lv2.GetValue():
            for key in sorted(self.lv2_dict.keys()):
                if filter_string in key.lower():
                    self.list_box_vst_lv2.Append(key)
        if event:
            event.Skip()

    def kill_apps(self, event):  # wxGlade: VstFrame.<event_handler>
        print('Running Kill Apps')
        comandos = ["kill -9 $(pgrep -f 'carla-bridge-native') &", "kill -9 $(pgrep -f 'jalv') &",
                    "kill -9 $(pgrep -f 'wine') &", "kill -9 $(pgrep -f '.exe') &"]
        return_values = ''
        for comando in comandos:
            return_value = os.popen(comando).read()
            return_values += return_value
        print(return_values)
        event.Skip()

    def load_dir_dialog(self):
        dlg = wx.DirDialog(None, "Choose directory", "",
                           wx.DD_DEFAULT_STYLE | wx.DD_DIR_MUST_EXIST)
        if dlg.ShowModal() == wx.ID_CANCEL:
            return  # the user changed their mind
        return dlg.GetPath()

    def vst2_select_new(self, event):  # wxGlade: VstFrame.<event_handler>
        new_dir = self.load_dir_dialog()
        if new_dir and new_dir not in self.vst2_dirs_list_config:
            self.vst2_dirs_list_config.append(new_dir)
            self.vst2_dirs_list_config.sort()
            self.load_config_vst2_listbox()
            self.config_json['vst2_dirs'] = self.vst2_dirs_list_config
            self.write_config()
        event.Skip()

    def vst2_remove(self, event):  # wxGlade: VstFrame.<event_handler>
        for item in self.list_box_vst2_directories.GetSelections():
            self.vst2_dirs_list_config.remove(self.list_box_vst2_directories.GetString(item))
        self.vst2_dirs_list_config.sort()
        self.load_config_vst2_listbox()
        self.config_json['vst2_dirs'] = self.vst2_dirs_list_config
        self.write_config()
        event.Skip()

    def vst3_select_new(self, event):  # wxGlade: VstFrame.<event_handler>
        new_dir = self.load_dir_dialog()
        if new_dir and new_dir not in self.vst3_dirs_list_config:
            self.vst3_dirs_list_config.append(new_dir)
            self.vst3_dirs_list_config.sort()
            self.load_config_vst3_listbox()
            self.config_json['vst3_dirs'] = self.vst3_dirs_list_config
            self.write_config()
        event.Skip()

    def vst3_remove(self, event):  # wxGlade: VstFrame.<event_handler>
        for item in self.list_box_vst3_directories.GetSelections():
            self.vst3_dirs_list_config.remove(self.list_box_vst3_directories.GetString(item))
        self.vst3_dirs_list_config.sort()
        self.load_config_vst3_listbox()
        self.config_json['vst3_dirs'] = self.vst3_dirs_list_config
        self.write_config()
        event.Skip()

    def set_keyboard_subtring(self, event):  # wxGlade: VstFrame.<event_handler>
        self.midi_keyboard_substring = self.text_ctrl_keyboard_substring.GetValue()
        self.config_json['keyboard_substring'] = self.midi_keyboard_substring
        self.write_config()
        event.Skip()

    def set_terminal(self, event):  # wxGlade: VstFrame.<event_handler>
        self.terminal = self.combo_box_terminal.GetString(self.combo_box_terminal.GetSelection())
        self.config_json['terminal'] = self.terminal
        self.write_config()
        event.Skip()

    def add_terminal(self, event):  # wxGlade: PluginFrame.<event_handler>
        new_terminal = self.combo_box_terminal.GetValue()
        if new_terminal and new_terminal not in self.combo_box_terminal.GetItems():
            confirm = wx.MessageBox(
                f'Do you want to add "{new_terminal}" to the Terminal list and select it?',
                'Confirm Add Terminal',
                wx.YES_NO | wx.ICON_QUESTION
            )
            if confirm == wx.YES:
                self.combo_box_terminal.Append(new_terminal)
                self.added_terminal_options.append(new_terminal)
                self.config_json['added_terminal_options'] = self.added_terminal_options
        self.config_json['terminal'] = new_terminal
        self.write_config()
        event.Skip()

    def set_autoconnect(self, event):  # wxGlade: VstFrame.<event_handler>
        self.repeat_retry_connection = int(
            self.combo_box_autoconnect_retry.GetString(self.combo_box_autoconnect_retry.GetSelection()))
        self.config_json['connect_retry'] = self.repeat_retry_connection
        self.write_config()
        event.Skip()

    def set_load_vst(self, event):  # wxGlade: PluginFrame.<event_handler>
        if self.load_vst != self.checkbox_load_vst.GetValue():
            self.load_vst = self.checkbox_load_vst.GetValue()
            self.config_json['load_vst'] = self.load_vst
            self.write_config()
            self.atualiza_listas()
        event.Skip()

    def set_load_lv2(self, event):  # wxGlade: PluginFrame.<event_handler>
        if self.load_lv2 != self.checkbox_load_lv2.GetValue():
            self.load_lv2 = self.checkbox_load_lv2.GetValue()
            self.config_json['load_lv2'] = self.load_lv2
            self.write_config()
            self.atualiza_listas()
        event.Skip()

    def set_interface_subtring(self, event):  # wxGlade: PluginFrame.<event_handler>
        self.interface_substring = self.text_ctrl_interface_substring.GetValue()
        self.config_json['interface'] = self.interface_substring
        self.write_config()
        event.Skip()

    def set_audioconnections(self, event):  # wxGlade: PluginFrame.<event_handler>
        self.audio_connections = int(
            self.combo_box_audio_connections.GetString(self.combo_box_audio_connections.GetSelection()))
        self.config_json['audio_connections'] = self.audio_connections
        self.write_config()
        event.Skip()


class MyApp(wx.App):
    def OnInit(self):
        self.frame = Plugin(None, wx.ID_ANY, "")
        self.SetTopWindow(self.frame)
        self.frame.Show()
        return True


# end of class MyApp

if __name__ == "__main__":
    print('Reading lv2ls...')
    plugin_standalone = MyApp(0)
    plugin_standalone.MainLoop()
