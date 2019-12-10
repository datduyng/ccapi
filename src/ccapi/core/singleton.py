class Singleton(type):
    instances = { }

    def __call__(self, *args, **kwargs):
        if self not in self.instances:
            super_ = super(Singleton, self)
            self.instances[self] = super_.__init__(*args, **kwargs)

        return self.instances[self]