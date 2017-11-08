click("1508420943640.png")
click("1508417628938.png")
click("1510076664358.png")
sleep(1)
type("v", KEY_CMD)
sleep(9)
click("1508420687346.png")
if exists("1508420854131.png"):
    click("1508948017257.png")
    type(Key.DOWN, KeyModifier.CMD)
    e1 = exists("1509354940989.png")
    if e1:
        t = find(Pattern("1509354953413.png").targetOffset(35,-1))
        click(t)
        click("1508421776272.png")
    else:
        click("1508421776272.png")
click(Pattern("1509031089016.png").targetOffset(11,-5))