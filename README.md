# uhu utility

## generate a name using unpaid robot labour

```xsh
@ buildsystem --build --clean --config ../config/custom/static/1.0.0/custom.yml -o test_build/ webapp/
🔨 Doing some shit...
😴 Wow that was hard
@ uhu # Shorten the command. May take a while the first time, as ollama has to load the model
✨ Last command shorened to 'buildcustom'
@ buildcustom  # Use the shortened name!
🔨 Doing some shit...
😴 Wow that was hard
```

## generate a name using unpaid human labour

```xsh
@ buildsystem --build --clean --config ../config/custom/static/1.0.0/custom.yml -o test_build/ webapp/
🔨 Doing some shit...
😴 Wow that was hard
@ uhu fuck
✨ Last command shorened to 'fuck'
```

## humans will take ai jobs / renaming

```xsh
@ buildsystem blah blah
🔨 Doing some shit...
😴 Wow that was hard
@ uhu
✨ Last command shorened to 'blowupyourcomputer'
@ uhu build # Don't like the name? Rename it!
✨ Renamed 'blowupyourcomputer' to 'build'
```


# install and config

```xsh
xpip install xontrib-uhu
```

```xsh
# $XONSH_UHU_SYSTEM_PROMPT = "..." # Optional! Only change if you know what you're doing!
# $XONSH_UHU_MAX_LLM_TRIES = 3  # Optional! 
# $XONSH_UHU_OLLAMA_URL = "http://ollama.myserver.internal" # Optional!

# MANDATORY (if you want to use it with ollama)! Using a coder model will likely help. 7b is probably enough.
$XONSH_UHU_MODEL_NAME = "qwen2.5-coder:7b"

xontrib load unreasonably_long
```

# limitations

Subprocess capture with uhu aliases doesn't work

# what does uhu even mean

> users hate unreasonablylongcommands

(Not really, I just wanted something which had a short name with the keys close together)


