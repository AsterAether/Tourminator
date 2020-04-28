from tourminator.bot import TourminatorBot

if __name__ == '__main__':

    with open('token.txt', 'r') as f:
        token = f.readline()

    client = TourminatorBot('!', 'tourminator.sqlite')
    client.run(token)
