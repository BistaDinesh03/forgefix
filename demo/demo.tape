# ForgeFix demo tape - recorded with vhs (charmbracelet/vhs).
# Every command here runs the REAL CLI; nothing in the output is staged.
#
#   make gif        # or: vhs demo/demo.tape
#
# The session works on a scratch copy of tests/fixtures/broken_repo so the
# fixtures themselves are never mutated (prep_scratch.py is cross-platform).

Set TypingSpeed 40ms
Set FontSize 16
Set Width 1000
Set Height 640
Set Theme "Dracula"
Set Padding 20
Set Framerate 12

Output demo/demo.gif

Type "echo ForgeFix - one command to fix any repo"
Enter
Sleep 1s
Type "echo ------------------------------------------------------------------"
Enter
Sleep 500ms

Type "forgefix --help"
Enter
Sleep 3s

Type "python demo/prep_scratch.py"
Enter
Sleep 1s
Type "cd demo-scratch"
Enter
Sleep 500ms

# Before: the broken fixture scores 42/100
Type "forgefix doctor"
Enter
Sleep 5s

# The report captures the same score
Type "forgefix report"
Enter
Sleep 3s

# One command repairs the setup, creates .venv, installs deps, runs tests
Type "forgefix up --apply"
Enter
Sleep 45s

# After: the same repo now scores 91/100
Type "forgefix doctor"
Enter
Sleep 5s
