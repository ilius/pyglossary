if __name__ == '__main__':
    import sys, os.path
    import glossary as gl
    glos = gl.Glossary()

    informat = gl.Glossary.descFormat["Babylon (bgl)"]
    outformat = gl.Glossary.descFormat["AppleDict Source (xml)"]

    filename = sys.argv[1]
    basename = os.path.splitext(os.path.basename(filename))[0]

    outdir = sys.argv[2]
    if not os.path.exists(outdir):
        os.mkdir(outdir)

    glos.read(filename, format=informat, resPath=os.path.join(outdir, "OtherResources"))

    glos.write(os.path.join(outdir, basename), format=outformat)

