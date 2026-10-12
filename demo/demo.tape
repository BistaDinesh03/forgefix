# ForgeFix demo tape - recorded with vhs (charmbracelet/vhs).
# Every command here runs the REAL CLI; nothing in the output is staged.
#
#   make gif     # writes demo/demo.gif and demo/demo.mp4
#
# The session works on a scratch copy of tests/fixtures/broken_repo, so the
# committed fixture is never mutated and the recording is re-runnable.
# Commands avoid `ls`/`dir` and quoting so the tape plays the same under
# vhs's default shell on Windows (cmd.exe) and on the Linux CI recorder.

Set FontFamily "JetBrains Mono"
Set FontSize 18
Set LineHeight 1.4
Set LetterSpacing 0
Set Width 1200
Set Height 700
Set Padding 40
Set Margin 20
Set MarginFill "#0F172A"
Set BorderRadius 12
Set Theme "Catppuccin Mocha"
Set WindowBar "Colorful"
Set WindowBarSize 40
Set TypingSpeed 45ms
Set Framerate 30
Set PlaybackSpeed 1.1

Output demo/demo.gif

# 1) Title card
Type "echo ForgeFix - one command to fix any repo's setup"
Enter
Sleep 2s

# 2) A deliberately broken repo: app.py + pyproject.toml, nothing else
#    (scratch copy, so the committed fixture stays pristine)
Type "python demo/prep_scratch.py"
Enter
Sleep 3s
Type "cd demo-scratch"
Enter
Sleep 1s

# 3) The health check: 42/100, every gap with a concrete fix
Type "forgefix doctor"
Enter
Sleep 3s

# 4) The same findings as markdown, highest-value fixes first
Type "forgefix report"
Enter
Sleep 2s

# 5) The bring-up: missing setup files, .venv, install, lockfile, tests
#    (outcomes print when the plan finishes, so this waits out the full run)
Type "forgefix up --apply"
Enter
Sleep 45s

# 6) The same repo, now healthy: 91/100
Type "forgefix doctor"
Enter
Sleep 3s

# 7) Final card
Type "echo github.com/BistaDinesh03/forgefix - pipx install forgefix"
Enter
Sleep 2s
