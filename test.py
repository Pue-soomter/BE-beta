
def func(test):
    test.app(10)

class template:
    def __init__(self):
        self.data=[]

    def app(self,test):
        self.data.append(test)

    def pr(self):
        print(self.data)



if __name__ == "__main__":

    a=template()
    func(a)
    a.pr()
