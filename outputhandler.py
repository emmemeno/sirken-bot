

# Split long text to shorter ones
class OutputHandler:
    def __init__(self, max_chars):
        self.max = max_chars
        self.splitted_text = []

    def cut(self, text: str):
        # if text length is below limit do not anything
        if len(text) < self.max:
            self.splitted_text.append(text)
            return self.splitted_text

        limit = text[0:self.max].rfind('\n')
        if limit == -1:
            limit = text[0:self.max].rfind(' ')
        self.splitted_text.append(text[0:limit+1])
        self.splitted_text.append(text[limit+1:])
        new_chunk = self.splitted_text[-1]
        if len(new_chunk) > self.max:
            self.splitted_text.pop()
            self.cut(new_chunk)

        return self.splitted_text

    def process(self, text):
        output = self.cut(text).copy()
        self.splitted_text.clear()
        return output

    def output_list(self, content: list):
        output = ""
        for line in content:
            output += line
        if output == "":
            output = "Empty! :("
        return output
