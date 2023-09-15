# Initialize an empty list to store the values
values = []

# Open the file for reading
with open("data.txt", "r") as file:
    # Loop through each line in the file
    for line in file:
        # Split the line into a list of strings using whitespace as theseparator
        parts = line.strip().split()

        # Convert the strings to floats and append them to the values list
        if len(parts) == 2:
            try:
                x = float(parts[0])
                y = float(parts[1])
                values.append((x, y))
            except ValueError:
                print(f"Skipping invalid line: {line}")

# Print the values
for value in values:
    print(value)