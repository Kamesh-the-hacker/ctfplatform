def text_to_whitespace_binary(text):
    binary_string = ""
    for char in text:
        # Convert each character to an 8-bit binary string (e.g., 'A' -> '01000001')
        char_binary = format(ord(char), "08b")
        binary_string += char_binary

    # Map 0 to \n (newline) and 1 to \t (tab) as requested
    whitespace_encoded = ""
    for bit in binary_string:
        if bit == "0":
            whitespace_encoded += "\n"
        elif bit == "1":
            whitespace_encoded += "\t"

    return whitespace_encoded


def main():
    # The flag/text you want to hide
    flag = "VHP{binary_is_zero_one}"

    # Encode the flag
    encoded_output = text_to_whitespace_binary(flag)

    # Save to a text file
    output_filename = "challenge.txt"
    with open(output_filename, "w", encoding="utf-8") as f:
        f.write(encoded_output)

    print(f"[+] Success! Challenge saved to '{output_filename}'")
    print(f"[+] Total bits hidden: {len(encoded_output)}")


if __name__ == "__main__":
    main()