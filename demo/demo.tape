# ForgeFix demo tape - recorded with vhs (charmbracelet/vhs).
# Every command here runs the REAL CLI; nothing in the output is staged.
#
#   make gif     # writes demo/demo.gif and demo/demo.mp4
#
# The session works on a scratch Node project so the recording is fast and
# re-runnable. It shows `up --apply` generating a Dockerfile and SECURITY.md,
# then `share` printing the ready-to-post panel.

Set FontFamily "JetBrains Mono"
Set FontSize 18
Set LineHeight 1.35
Set LetterSpacing 0
Set Width 1200
Set Height 700
Set Padding 32
Set Margin 16
Set MarginFill "#0F172A"
Set BorderRadius 12
Set Theme "Catppuccin Mocha"
Set WindowBar "Colorful"
Set WindowBarSize 36
Set TypingSpeed 25ms
Set Framerate 30
Set PlaybackSpeed 1.1

Output demo/demo.gif

# 1) Title card
Type "echo ForgeFix 0.3.0 - setup health, fixed in one command"
Enter
Sleep 1s

# 2) A tiny Node project with a missing setup and a process.env reference
Type "python demo/prep_scratch.py"
Enter
Sleep 1.2s
Type "cd demo-scratch"
Enter
Sleep 0.5s

# 3) Real bring-up: generate files, install, lock, test
Type "forgefix up --apply --yes --no-serve"
Enter
Sleep 10s

# 4) Show the generated SECURITY.md and stack-specific Dockerfile
Type "python ../demo/show_generated.py"
Enter
Sleep 3.5s

# 5) The share panel, including the repo and demo-GIF links
Type "forgefix share --repo-url https://github.com/BistaDinesh03/forgefix"
Enter
Sleep 4s

# 6) Final card
Type "echo github.com/BistaDinesh03/forgefix - pipx install forgefix"
Enter
Sleep 1.5s
