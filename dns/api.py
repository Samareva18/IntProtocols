import argparse
import requests

API_VERSION = "5.131"


class VKApi:
    def __init__(self, access_token):
        self.access_token = access_token

    def get_friends(self, user_id):
        params = {
            'user_id': user_id,
            'fields': 'first_name,last_name',
            'access_token': self.access_token,
            'v': API_VERSION
        }

        response = requests.get("https://api.vk.com/method/friends.get", params=params).json()
        friends = response.get('response', {}).get('items', [])
        return friends

    def print_friends(self, friends):
        for idx, friend in enumerate(friends, start=1):
            print(f"{idx}. {friend['first_name']} {friend['last_name']}")


def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--access_token", help="VK API access token")
    parser.add_argument("--user_id", help="VK user ID")
    return parser.parse_args()


def main():
    args = get_args()
    if not args.access_token:
        args.access_token = input("Access token: ")

    if not args.user_id:
        args.user_id = input("User ID: ")

    try:
        api = VKApi(args.access_token)

        friends = api.get_friends(args.user_id)
        api.print_friends(friends)

    except KeyboardInterrupt:
        exit()


if __name__ == '__main__':
    main()

    #vk1.a.501ikQJ9e9VEj4dE7ZykHd2jsqc4sRe0A5y0zTrSKLpajmCRYSa5ZR_JM__YioJDxsSf4EuIaj22fhlgUczQTfUcwa4wd2SbWJYrSbiKWhD15_WQYtJyCBOdN0tnVwbw87K27abnC6N57aQ7vCCqBQkdi-naxasiDcwo4yg4OnaZ6lLu_kURJKR9nTgg_DnrsBOOuiD34UpSI5Sboy2yIw
    #391575965