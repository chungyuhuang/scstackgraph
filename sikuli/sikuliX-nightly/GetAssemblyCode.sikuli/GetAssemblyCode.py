click("1508420943640.png")
click("1508417628938.png")
click("1508421060778.png")
sleep(2)
type("v", KEY_CMD)
sleep(10)
click("1508420687346.png")
if exists("1508420854131.png"):
    click("1508948017257.png")
    type(Key.DOWN, KeyModifier.CMD)
    e1 = exists(Pattern("1508421204819.png").targetOffset(46,0))
    if e1:
        t = find(Pattern("1508421204819.png").targetOffset(46,0))
        click(t)
        click("1508421776272.png")
    else:
        click("1508421776272.png")
click(Pattern("1509031089016.png").targetOffset(11,-5))