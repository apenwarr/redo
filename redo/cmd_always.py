import sys, os
import vars, state


def main():
    try:
        me = os.path.join(vars.STARTDIR,
                          os.path.join(vars.PWD, vars.TARGET))
        f = state.File(name=me)
        f.add_dep('m', state.ALWAYS)
        always = state.File(name=state.ALWAYS)
        always.stamp = state.STAMP_MISSING
        always.set_changed()
        always.save()
        state.commit()
    except KeyboardInterrupt:
        sys.exit(200)


if __name__ == '__main__':
    main()
