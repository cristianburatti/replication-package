from progress.bar import Bar


class ProgressBar:
    def __init__(self, df):
        self.max = df.shape[0]
        self.count = 1
        self.bar = Bar('Processing', max=self.max)

    def update(self, *info):
        info = [str(i) for i in info]
        progress = f'{self.count}/{self.max} ({float(self.count) / float(self.max) * 100:.2f}%%)'
        time = f'{self.bar.elapsed_td}'
        self.bar.suffix = f'{progress} | {time}{" | " + " | ".join(info) if info else ""}'

    def next(self):
        self.count += 1
        self.bar.next()

    def finish(self):
        self.bar.finish()
