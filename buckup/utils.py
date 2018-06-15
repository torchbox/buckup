class CommandLineInterface:
    def ask(self, question):
        return input('{}\n>>> '.format(question))

    def ask_yes_no(self, question, default=None):
        if default is True:
            options = '[Y/n]'
        elif default is False:
            options = '[y/N]'
        else:
            options = '[y/n]'
        answer = self.ask('{} {}'.format(question, options))
        if not answer:
            if default is True:
                answer = 'y'
            elif default is False:
                answer = 'n'
            elif default is None:
                return self.ask_yes_no(question, default=default)
        if answer.lower() == 'y':
            return True
        elif answer.lower() == 'n':
            return False
        return self.ask_yes_no(question, default=default)
