from datetime import datetime

import vk_api
from vk_api.exceptions import ApiError

from config import access_token


class VkTools:
    def __init__(self, access_token):
        self.api = vk_api.VkApi(token=access_token)

    def _bdate_to_year(self, bdate):
        if bdate is None:
            return None
        user_bdate_list = bdate.split('.')
        bdate_day, bdate_month, bdate_year = user_bdate_list
        curr_date = datetime.now().date()
        age = curr_date.year - int(bdate_year)
        if curr_date.month < int(bdate_month)\
                or (curr_date.month == int(bdate_month) and curr_date.day < int(bdate_day)):
            age = age - 1
        return age

    def get_profile_info(self, current_user_id):
        try:
            info, = self.api.method('users.get',
                                      {
                                          'user_id': current_user_id,
                                          'fields': 'city,bdate,sex,relation,home_town'
                                      }
                                      )
        except ApiError as error:
            info = {}
            print(f'Произошла ошибка = {error}')

        result = {
            'name': f'{info["first_name"]} {info["last_name"]}' if 'first_name' in info and 'last_name' in info else None,
            'sex': info.get("sex"),
            'city': info.get("city")["title"] if 'city' in info else None,
            'year': self._bdate_to_year(info.get("bdate"))
        }
        return result

    def search_worksheet(self, profile, offset):
        try:
            users = self.api.method('users.search',
                                      {
                                          'count': 50,
                                          'offset': offset,
                                          'hometown': profile['city'],
                                          'sex': 1 if int(profile['sex']) == 2 else 2,
                                          'has_photo': True,
                                          'age_from': int(profile['year']) - 3,
                                          'age_to': int(profile['year']) + 3,
                                          'status': 6
                                       }
                                      )
        except ApiError as error:
            users = []
            print(f'Произошла ошибка = {error}')

        result = [
            {
                'name': f'{user["first_name"]} {user["last_name"]}',
                'id': user['id']
            } for user in users['items'] if user['is_closed'] is False
        ]
        return result

    def get_photos(self, photo_id):
        try:
            photos_list = self.api.method('photos.get',
                                      {'owner_id': photo_id,
                                       'album_id': 'profile',
                                       'extended': 1
                                       }
                                      )
        except ApiError as error:
            photos_list = {}
            print(f'Произошла ошибка = {error}')

        result = [
            {
                'owner_id': photo['owner_id'],
                'id': photo['id'],
                'likes': photo['likes']['count'],
                'comments': photo['comments']['count']
            } for photo in photos_list['items']
        ]

        return sorted(result, key=lambda i: i['likes'] + i['comments'], reverse=True)[:3]





