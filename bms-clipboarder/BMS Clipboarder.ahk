
;^d::
;  CopyNotes()
;  RunUtility("dist\build\Unmatch\Unmatch.exe")
;  Return

;^m::
;  InputBox script, Move notes, Enter script (a)[z][s][x][d][c][f][v]
;  Sleep 200
;  CutNotes()
;  RunUtility("dist\build\MoveNotes\MoveNotes.exe """ . script . """")
;  Return

^b::
  CutNotes()
  ;RunUtility("dist\build\BGMize\BGMize.exe")
  RunUtility("python bgmize.py")
  Return

!^m::
  CutNotes()
  RunUtility("python sidemines.py")
  Return

^l::
  _PrepareClipboard("Copy", "match1.txt")
  Return

^+l::
  _PrepareClipboard("Cut", "match2.txt")
  RunWait %comspec% /c python patternmatch.py > output.txt, , Min
  Sleep 100
  FileRead Clipboard, output.txt
  Send ^v
  Return

!^l::
  _PrepareClipboard("Cut", "match2.txt")
  RunWait %comspec% /c python soundmatch.py > output.txt, , Min
  Sleep 100
  FileRead Clipboard, output.txt
  Send ^v
  Return

CopyNotes()
{
  _PrepareClipboard("Copy", "input.txt")
}

CutNotes()
{
  _PrepareClipboard("Cut", "input.txt")
}

RunUtility(utility)
{
  RunWait %comspec% /c %utility% < input.txt > output.txt, , Min
  FileRead output, *t output.txt
  lines := StrSplit(output, "`n")
  status := lines.RemoveAt(1)
  message := lines.RemoveAt(1)
  If (status = "ok")
  {
    outClipboard := ""
    Loop % lines.MaxIndex()
    {
      outClipboard .= lines[A_Index] . "`r`n"
    }
    Clipboard := outClipboard
    Sleep 100
    Send ^v
  }
  Else
  {
    MsgBox bms-clipboarder ERROR %status%: %message%
  }
}

_PerformClipboardOperation(mode)
{
  If (mode = "Copy")
  {
    Send ^c
  }
  If (mode = "Cut")
  {
    Send ^x
  }
}

_PrepareClipboard(mode, file)
{
  Clipboard := "!"
  Sleep 100
  _PerformClipboardOperation(mode)
  While Clipboard == "!"
  {
  }
  FileDelete %file%
  FileAppend %Clipboard%, %file%, UTF-8-RAW
}
