from progress.bar import Bar


class ProgressBar:
    """
    Progress bar class
    """
    def __init__(self, df):
        self.max = df.shape[0]
        self.count = 0
        self.current_description = ''
        self.bar = Bar('Processing', max=self.max)

    def update(self, *info):
        """
        Update the progress bar
        To be called at the start of each iteration
        :param info: all the information to be displayed
        """

        progress = f'{self.count}/{self.max} ({float(self.count) / float(self.max) * 100:.2f}%%)'
        time = f'{self.bar.elapsed_td}'
        if info:
            self.current_description = ' | ' + ' | '.join(info)
        self.bar.suffix = f'{progress} | {time} {self.current_description}'

    def next(self):
        """
        Increment the progress bar
        To be called at the end of each iteration
        """

        self.count += 1
        self.bar.next()

    def finish(self):
        """
        Finish the progress bar
        To be called after the last iteration
        """

        self.update()
        self.next()
        self.bar.finish()
