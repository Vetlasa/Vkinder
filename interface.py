import vk_api
from vk_api.longpoll import VkLongPoll, VkEventType
from vk_api.utils import get_random_id

from config import comunity_token, access_token
from core import VkTools
from data_base import check_user, add_user


class BotInterface:
    def __init__(self, comunity_token, user_token):
        self.vk = vk_api.VkApi(token=comunity_token)
        self.longpoll = VkLongPoll(self.vk)
        self.vk_tools = VkTools(user_token)
        self.params = {}
        self.worksheets = []
        self.offset = 0

    def _get_profile_data(self):
        worksheet = self.worksheets.pop()
        photos = self.vk_tools.get_photos(worksheet['id'])
        photo_str = ''

        for photo in photos:
            photo_str += f'photo{photo["owner_id"]}_{photo["id"]},'

        return {
            'name': worksheet["name"],
            'id': worksheet["id"],
            'photo': photo_str
        }

    def _check_worksheets_len(self):
        if not self.worksheets:
            self.worksheets = self.vk_tools.search_worksheet(self.params, self.offset)
            self.offset += 50

    def _get_required_data(self, user_id, key):
        messages = {
            'name': 'Необходимо указать свои имя и фамилию',
            'sex': 'Необходимо указать свой пол в формате: 1 - женщина, 2 - мужчина',
            'city': 'Необходимо указать город поиска',
            'age': 'Необходимо указать свой возраст(сколько полных лет)'
        }

        self.message_send(user_id, messages[key])
        for event in self.longpoll.listen():
            if event.type == VkEventType.MESSAGE_NEW and event.to_me:
                self.params[key] = event.text
                return

    def message_send(self, user_id, message, attachment=None):
        self.vk.method('messages.send',
                       {
                           'user_id': user_id,
                           'message': message,
                           'attachment': attachment,
                           'random_id': get_random_id()
                       }
                       )

    def event_handler(self):
        for event in self.longpoll.listen():
            if event.type == VkEventType.MESSAGE_NEW and event.to_me:
                if event.text.lower() == 'привет':
                    self.params = self.vk_tools.get_profile_info(event.user_id)
                    self.message_send(event.user_id, f'Здравствуй, {self.params["name"]}!\n'
                                                     f'Я бот VKinder! \n'
                                                     f'Я знаю команды: \n'
                                                     f'"Поиск" - поиск людей в твоем городе \n'
                                                     f'в возрастном диапазоне +5 и -5 года\n'
                                                     f'от твоей даты рождения.\n'
                                                     f'"Пока" - конец поиска\n'
                                                     )

                elif event.text.lower() == 'поиск':
                    for item in self.params:
                        if self.params[item] is None:
                            self._get_required_data(event.user_id, item)

                    self.message_send(event.user_id, 'Минуточку..')
                    self._check_worksheets_len()

                    found_profile = self._get_profile_data()
                    ununique_user = check_user(event.user_id, found_profile["id"])

                    if ununique_user:
                        while ununique_user:
                            found_profile = self._get_profile_data()
                            ununique_user = check_user(event.user_id, found_profile["id"])
                            self._check_worksheets_len()

                    self.message_send(event.user_id,
                                      f'Имя: {found_profile["name"]}\n'
                                      f'Ссылка на страницу: https://vk.com/id{found_profile["id"]}',
                                      attachment=found_profile["photo"]
                                      )
                    add_user(event.user_id, found_profile["id"])

                elif event.text.lower() == 'пока':
                    self.message_send(event.user_id, 'Пока')
                else:
                    self.message_send(event.user_id,
                                      'Неизвестная команда(((\n'
                                      'Список доступных команд:\n'
                                      '\\привет\n'
                                      '\\поиск\n'
                                      '\\пока')


if __name__ == '__main__':
    bot_interface = BotInterface(comunity_token, access_token)
    bot_interface.event_handler()
