import subprocess

du = subprocess.run(["df", "/"],
    capture_output=True,
    text=True)

print(int(du.stdout.splitlines()[1].split()[4][:-1]))

if int(du.stdout.splitlines()[1].split()[4][:-1]) > 12:
  print("bigger than 12")



#capture the whole output of "df /". split it into lines a grab the second line. Split that on the whitespaces and grab the 5th data. Remove the % from the end. Turn it into an int

