
class Continuation:
    def __init__(self,file_description):
        self.file_description = file_description
        self.contents_list = list()
        for contents in file_description:
            check = contents.split(",")
            if check[0] != '"':
                self.contents_list.append(check)
        #TODO:you might want to put a for loop that takes of the \n char from the list

    def get_file_contents(self):
        return self.contents_list
    def get_description_contents(self):
        return self.contents_list[1:7]

    def get_file_specifications(self):
        return self.contents_list[7:]

    def get_hex_list(self,with_whitespace = False,with_family_code = False):
        hex_list= list()
        if with_whitespace:
            for contents in range(10,len(self.contents_list)):
                if "-" not in self.contents_list[contents][-1]:
                    if with_family_code:
                        grab_hex = self.contents_list[contents][-1][:-1]+" 28"
                    else:
                        grab_hex = self.contents_list[contents][-1][:-1]
                    hex_list.append(grab_hex)
        else:
            for contents in range(10,len(self.contents_list)):
                if "-" not in self.contents_list[contents][-1]:
                    grab_hex = self.contents_list[contents][-1][:-1].replace(" ","")+"28"
                    turn_hex_to_int = int(grab_hex,16)
                    hex_list.append(turn_hex_to_int)
        return hex_list