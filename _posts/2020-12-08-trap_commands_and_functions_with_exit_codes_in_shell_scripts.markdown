---
layout: post
title: Trap Commands and Functions with Exit Codes in Shell Scripts
date: 2020-12-08 00:50:10 -0800
comments: true
---

# Trap Commands and Functions with Exit Codes in Shell Scripts

All sorts of secrets storage access is possible with modern clould continuous integration environment for you these days.  But what if you faced this issue inside the context of a Jenkins server you had control over?

We have a local build machine and a remote deploy machine, and we need to run a remote application that requires a username and password.  The username and password exist as environment variables in the local build machine process.

![](/images/trap-command-setup.png "trap-command-setup"){: width="900" }

How should we safely and securely get the credentials to the remote application as environment variables on the remote machine?


## Trap Functions / Command in Bash
[Trap functions in bash scripting]([https://www.putorius.net/using-trap-to-exit-bash-scripts-cleanly.html]) are a way of running commands no matter whether a script terminates successfully or not, or in reaction to specific signals if desired.

An example:

```bash
#!/bin/bash
function lands_on_feet {
  echo "I landed on my feet, meow."
}

trap lands_on_feet EXIT

echo "I'm a cat."

exit 0
# try exit 1 as well

```

The cat will always (EXIT means "always run the trap")land on its feet.

You can also use a command directly: `trap "echo \"I landed on my feet, meow.\"" EXIT` rather than a function.

There are two gotchas:

First gotcha: what if we care a lot about how we get our exit code?
Since sometime the trap function is the last command to run, you'll want to be sure to make the trap function return the exit status of the last SCRIPTED command OUTSIDE the trap - that's the real exist status you want most often.  So you'll [want to preserve the exit code](https://stackoverflow.com/questions/5312266/how-to-trap-exit-code-in-bash-script).

Second gotcha: the `trap` command will only catch failures below where it is declared - any scripting commands BEFORE the trap will not be subject to the trap.

## Back to Our Problem

Let's attack this problem using temporary script files.
* quietly write the credentials we need to a temporary script,
* copy and run that script on the remote machine
* this sets the environment variables in the remote shell.
* then, run  the remote application and pick up the credentials.

This will work, and not reveal our credentials on the process command line.However, we will want to be sure to wipe out the local and remote credentials scripts lest prying eyes see the files.  You guessed it, we will be using a trap function.

First, let's establish file names, and ensure a  quiet logging environment in case our build script is logging commands:

```bash
set +x
LOCAL_CREDENTIALS_FILE=$(mktemp -d)/.credentials.sh
REMOTE_CREDENTIALS_FILE=.credentials.sh
```

Now we can ensure we remove the local credentials file, preserving the exit status of the last scripted command.  Let's remove the remote credentials as well, in case something goes wrong, for good measure.

```bash
function exit_handler {
  rv=\$?
  rm ${LOCAL_CREDENTIALS_FILE}
  ssh -l remoteuser@{REMOTE_MACHINE} "rm -f ${REMOTE_CREDENTIALS_FILE}"
  return \$rv
}

trap exit_handler EXIT

```

Then we write out the credentials file, and copy it to the remote machine.

```bash
cat >${LOCAL_CREDENTIALS_FILE}<<EOF
#!/bin/bash
export credentials=user:password
EOF
set -x

scp ${LOCAL_CREDENTIALS_FILE} remoteuser@${REMOTE_MACHINE}:${REMOTE_CREDENTIALS_FILE}
```

When we run the application on the remote machine, let's run it with a trap on the remote machine to clean up the file.  The `sudo -E` is to remind us to preserve the environment for the application inside the sudo shell, in case that applies to your case.

```bash

ssh -l remoteuser@{REMOTE_MACHINE} "
    trap "rm -f ${REMOTE_CREDENTIALS_FILE}" EXIT ; \
    . ./${REMOTE_CREDENTIALS_FILE} ; \
    sudo -E run_remote_application "

```

Putting it all together we have:

```bash
set +x
LOCAL_CREDENTIALS_FILE=$(mktemp -d)/.credentials.sh
REMOTE_CREDENTIALS_FILE=.credentials.sh

function exit_handler {
  rv=\$?
  rm ${LOCAL_CREDENTIALS_FILE}
  ssh -l remoteuser@{REMOTE_MACHINE} "rm -f ${REMOTE_CREDENTIALS_FILE}"
  return \$rv
}

trap exit_handler EXIT

cat >${LOCAL_CREDENTIALS_FILE}<<EOF
#!/bin/bash
export credentials=user:password
EOF
set -x

scp ${LOCAL_CREDENTIALS_FILE} remoteuser@${REMOTE_MACHINE}:${REMOTE_CREDENTIALS_FILE}

ssh -l remoteuser@{REMOTE_MACHINE} "
    trap "rm -f ${REMOTE_CREDENTIALS_FILE}" EXIT ; \
    . ./${REMOTE_CREDENTIALS_FILE} ; \
    sudo -E run_remote_application "


```


## Some Quick Experimenting

What had me concerned about this approach is I wanted to make sure the exit status code from the remote system were preserved (and of course the files were cleaned).

So I wrote some quick tests.
```bash
# Expect 20
ssh remote_machine \
  'trap "echo \"Leaving now.\" exit 20" EXIT ; exit 10'
echo $?

#Expect 10
ssh remote_machine \
  'trap "rv=\$?; echo \"Leaving now.\" exit \$rv" EXIT ; exit 10'
echo $?

# Expect to see the file and have it be removed.
scp some_file remote_machine:
ssh remote_machine 'trap \"rm -f some_file; ls -al\" EXIT ; ls -al'

```


# Conclusion

OK, look I admit this is not infinitely secure.  The credentials do only live for the lifetime of the build script though, and do not show up on a command line.

More thorough approaches would be to store encrypted credentials on each remote machine, and use a HSM (hardware security module) to  decrypt them on demand.  Even then, one would need to either do that in-application-process or be faced with how to get them into the environment of the running application on the remote machine.

So, if you're not a high security project like a bank, and you're rolling your own Jenkins jobs for a cheaper controllable CI experience, this is one way to go.
