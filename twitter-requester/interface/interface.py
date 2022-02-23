import PySimpleGUI as sg
from extractor.extractor import Lookup, QueryBuilder
from api.api import ApiError
import csv
from datetime import date
import math
import traceback

class tweetsHandler():

    @staticmethod
    def export_tweets(tweets, name):
        with open(name + '.csv', 'w+', encoding='utf-8', newline='') as file:
            writer = csv.writer(file, delimiter=';', quoting=csv.QUOTE_ALL)
            writer.writerow(["id", "text", "created_at", "author_id", "author_name", "like_count", "retweet_count", "quote_count", "reply_count", "retweet_of_id", "quote_of_id", "reply_to_id"])
            for tweet in tweets:
                writer.writerow([tweet.id, tweet.text.replace("\"", "'"), tweet.created_at, tweet.author_id, tweet.author.name, tweet.public_metrics.like_count, tweet.public_metrics.retweet_count, tweet.public_metrics.quote_count, tweet.public_metrics.reply_count, tweet.retweet_of, tweet.quote_of, tweet.reply_of])

class GUI():

    def createButton(self, text):
        return sg.Button(text, font=self.font, button_color=self.defaultColor, mouseover_colors=(self.fontColor, self.colorOnClick))

    def createCheckbox(self, text, key):
        return sg.Checkbox(text, key=key, font=self.font, enable_events=True, background_color=self.backgroundColor)

    def createRadio(self, text, group, key):
        return sg.Radio(text, group, key=key, font=self.font, enable_events=True, background_color=self.backgroundColor)

    def __init__(self):
        self.keywords = list()
        self.fontColor = '#ffffff'
        self.defaultColor = '#1DA1F2'
        self.colorOnClick = '#098dde'
        self.backgroundColor = '#14171A'
        self.font = 'Arial 12 bold'
        self.layout = [
            [sg.Text('Digite um termo de busca', key='-QueryWord-', font=self.font, background_color=self.backgroundColor)],
            [sg.Input(key='-key-', do_not_clear=False, font=self.font)],
            [self.createButton('Adicionar termo'), self.createButton('Remover termo'), self.createButton('Limpar termos')],
            [sg.Listbox(self.keywords, key='-Listbox-', font=self.font, size=(50, 10), tooltip='Todos esses termos serão buscados.', background_color='#E1E8ED')],
            [sg.Input(key='-since-', size=(9,1), font=self.font), sg.CalendarButton('Data início',  target='-since-', button_color=self.defaultColor, default_date_m_d_y=(2,None,2020), locale='pt_BR', begin_at_sunday_plus=1, font=self.font), sg.Input(key='-to-', size=(9,1), font=self.font), sg.CalendarButton('Data final',  target='-to-',  default_date_m_d_y=(2,None,2020), locale='pt_BR', begin_at_sunday_plus=1, font=self.font, button_color=self.defaultColor), sg.Text('Nº tweets', key='-NTweets-', font=self.font, background_color=self.backgroundColor), sg.Input(key='-notweets-', size=(5,1), do_not_clear=False, font=self.font)],
            [self.createCheckbox('Remover retweets', '-Retweets-'), self.createCheckbox('Remover replies', '-Replies-'), self.createCheckbox('Remover quotes', '-Quotes-')],
            [self.createRadio('Apenas retweets', 'Radio1', '-OnlyRetweets-'), self.createRadio('Apenas replies', 'Radio1', '-OnlyReplies-'), self.createRadio('Apenas quotes', 'Radio1', '-OnlyQuotes-'), sg.Button('↺', font='Arial 14 bold', button_color=self.defaultColor, mouseover_colors=(self.fontColor, self.colorOnClick))],
            [sg.Button('Procurar tweets', font=self.font, size=(46, 1), button_color=self.defaultColor, mouseover_colors=(self.fontColor, self.colorOnClick))]
        ]
        self.window = sg.Window('Twittery', self.layout, background_color=self.backgroundColor, element_justification='c')

    def buildQuery(self, event, values):
        if event != 'Procurar tweets':
            return
        queryBuilder = QueryBuilder()
        query = queryBuilder.build(self.keywords, retweets_only=values['-OnlyRetweets-'], replies_only=values['-OnlyReplies-'], quotes_only=values['-OnlyQuotes-'], del_retweets=values['-Retweets-'], del_replies=values['-Replies-'], del_quotes=values['-Quotes-'])
        lookup = Lookup()
        if values["-notweets-"] != None and values["-notweets-"] != "":
            total = int(values["-notweets-"])
        else:
            total = 1000
        try:
            tweetsHandler.export_tweets(lookup.get_archive_tweets(query, start_time=values["-since-"], end_time=values["-to-"], npages=math.ceil(total/500), max_results=500), 'datasets/' + 'df-' + str(date.today()))
            sg.popup("Amostra de tweets gerada com sucesso.")
        except ApiError as e:
            error = str(e)
            if '400' in error:
                sg.popup_error(f'O campo de palavras chaves está vazio.')
            if '429' in error:
                sg.popup_error(f'Número muito alto de chamadas em pouco tempo. Tente novamente em alguns minutos.')
            if '523' in error:
                sg.popup_error(f'O Twitter parece estar indisponível.')
            sg.popup_error(f'Algum erro aconteceu ao chamar a API.', e, traceback.format_exc())
        except Exception as e:
            sg.popup_error(f'Algum erro inesperado ocorreu. O log está disponível na pasta logs.', e, traceback.format_exc())

    def noRadiosTrue(self, values):
        keys = ['-OnlyRetweets-', '-OnlyReplies-', '-OnlyQuotes-']
        for key in keys:
            if values[key]:
                return False
        return True

    def handleCheckboxes(self, event, values):
        events = ['-Retweets-', '-Replies-', '-Quotes-']
        if event in events and not self.noRadiosTrue(values):
            self.window[event].update(False)

    def noCheckboxesTrue(self, values):
        keys = ['-Retweets-', '-Replies-', '-Quotes-']
        for key in keys:
            if values[key]:
                return False
        return True

    def turnCheckboxesOff(self):
        self.window['-Retweets-'].update(False)
        self.window['-Replies-'].update(False)
        self.window['-Quotes-'].update(False)

    def turnRadioOff(self):
        self.window['-OnlyRetweets-'].update(False)
        self.window['-OnlyReplies-'].update(False)
        self.window['-OnlyQuotes-'].update(False)

    def handleOptions(self, event, values):
        if event == '↺':
            self.turnRadioOff()
            self.turnCheckboxesOff()
        events = ['-OnlyRetweets-', '-OnlyReplies-', '-OnlyQuotes-']
        if event in events and not self.noCheckboxesTrue(values):
            self.window[event].update(False)

    def handleList(self, event, values):
        if event == 'Adicionar termo' and values['-key-'] != '':
            self.keywords.append(values['-key-'])
            self.window['-Listbox-'].update(self.keywords)
        if event == 'Remover termo' and len(self.keywords) > 0:
            listbox = self.window['-Listbox-'].TKListbox
            if listbox.curselection():
                value = listbox.get(listbox.curselection())
                self.keywords.remove(value)
                self.window['-Listbox-'].update(self.keywords)
        if event == 'Limpar termos':
            self.keywords.clear()
            self.window['-Listbox-'].update([])

    def handler(self):
        while True:
            event, values = self.window.read()
            if event == sg.WIN_CLOSED:
                break
            self.handleList(event, values)
            self.handleOptions(event, values)
            self.handleCheckboxes(event, values)
            self.buildQuery(event, values)
            self.window.refresh()
        self.window.close()

    def create(self):
        self.handler()

def invokeInterface():
    interface = GUI()
    interface.create()

def main():
    invokeInterface()

if __name__ == "__main__":
    main()