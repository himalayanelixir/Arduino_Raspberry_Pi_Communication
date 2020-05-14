#!/home/pi/code/pi_env/bin/python3
# Copyright 2020 Harlen Bains
# linted using pylint
# formatted using black
"""This script runs on the Raspberry Pi and sends commands to Arduinos.
Once a command is sent it then waits a reply and then loops.
"""

from threading import Thread
import serial  # pylint: disable=import-error
from yaspin import yaspin  # pylint: disable=import-error
from yaspin.spinners import Spinners  # pylint: disable=import-error
import timeout_decorator  # pylint: disable=import-error


class Error(Exception):
    """Exception that is raised when an error occurs in the program
    causes the program to print out a message and then loop.
    """


def execute_commands(serial_ports, command_string_execute):
    """Creates threads that send commands to the Arduinos and wait for replies.
    there is one thread for each Arduino.

    Args:
      serial_ports: List containing address of USB ports, pySerial object, array number,
        and number of motors.
      command_string_execute: String of commands that are to be sent to all the arrays.
    """
    parse_text = command_string_execute.split(";")
    threads = [None] * len(serial_ports)
    SPINNER.start()
    # create threads
    for count, _ in enumerate(parse_text):
        threads[count] = Thread(
            target=move_arrays, args=(serial_ports, parse_text[count], count)
        )
        # start threads
        threads[count].start()
    # wait for threads to finish
    for count, _ in enumerate(parse_text):
        threads[count].join()
    SPINNER.stop()


def open_ports(serial_ports):
    """Open ports and create pySerial objects saving them to serial_ports.

    Args:
      serial_ports: List containing address of USB ports, pySerial object, array number,
        and number of motors.

    Returns:
      Returns a list with serial_ports data but with the pySerial object added for each array.

    Raises:
      Error: If pySerial object cannot be created.
    """
    print("\nOpening Port(s)")
    SPINNER.start()
    # go through serial_ports list and try to connect to usb devices
    # otherwise error
    for count, _ in enumerate(serial_ports):
        try:
            serial_ports[count] = [
                serial_ports[count],
                serial.Serial(serial_ports[count], BAUD_RATE),
            ]
            SPINNER.write(
                "Serial Port "
                + str(count)
                + " "
                + serial_ports[count][0]
                + " \033[32m"
                + "READY"
                + "\033[0m"
            )
        except serial.serialutil.SerialException:
            SPINNER.write(
                "Serial Port "
                + str(count)
                + " "
                + serial_ports[count][0]
                + " \033[31m"
                + "FAILED"
                + "\033[0m"
            )
            SPINNER.stop()
            raise Error
    SPINNER.stop()
    return serial_ports


def connect_to_arrays(serial_ports):
    """Connect to arrays and retrieve connection message.

    Args:
      serial_ports: List containing address of USB ports, pySerial object, array number,
        and number of motors.

    Returns:
      Returns a list with serial_ports data but with array number and number of motors
        filled in for each array.

    Raises:
      Error: If the correct message is not recived within timeout.
    """
    print("\nConnecing to Arrays")
    # used for thread objects
    connection_threads = [None] * len(serial_ports)
    # used to store returned values from threads
    results = [None] * len(serial_ports)
    SPINNER.start()
    # create threads
    for count, _ in enumerate(serial_ports):
        connection_threads[count] = Thread(
            target=wait_for_arduino_connection, args=(serial_ports, count, results)
        )
        # start threads
        connection_threads[count].start()

    # wait for threads to finish
    for count, _ in enumerate(serial_ports):
        connection_threads[count].join()
    SPINNER.stop()
    # get returned values from threads and assign to serial_port
    for count_row, row in enumerate(results):
        if row[0]:
            raise Error
        serial_ports[count_row] = row[1]
    return serial_ports


def wait_for_arduino_connection(serial_ports, port, results):
    """Wait until the Arduino sends "Arduino Ready" - allows time for Arduino
    reset it also ensures that any bytes left over from a previous message are
    discarded.

    Args:
      serial_ports: List containing address of USB ports, pySerial object, array number,
        and number of motors.
      port: Thread number created from enumerating through serial_ports.
      results: Used to find if errors occoured in the thread and pass back to connect_to_arrays().
    """
    error = False
    try:
        wait_for_arduino_connection_execute(serial_ports, port)
        SPINNER.write("Serial Port " + str(port) + " \033[32m" + "READY" + "\033[0m")
    except timeout_decorator.TimeoutError:
        error = True
        SPINNER.write(
            "Serial Port "
            + str(port)
            + " \033[31m"
            + "FAILED: WAITING FOR MESSAGE TIMEOUT"
            + "\033[0m"
        )
    except IndexError:
        error = True
        SPINNER.write(
            "Serial Port "
            + str(port)
            + " \033[31m"
            + "FAILED: NEGATIVE ARRAY NUMBER OR MOTOR NUMBER PASSED"
            + "\033[0m"
        )
    # works as a return functon for the thread
    results[port] = [error, serial_ports[port]]


@timeout_decorator.timeout(10, use_signals=False)
def wait_for_arduino_connection_execute(serial_ports, port):
    """Waits for Arduino to send ready message. Created so we can have a
    timeout and a try catch block.

    Args:
      serial_ports: List containing address of USB ports, pySerial object, array number,
        and number of motors.
      port: Thread number created from enumerating through serial_ports.

    Returns:
      Array number and the number of motors conntected to it.
    """
    msg = ""
    while msg.find("Arduino is ready") == -1:
        while serial_ports[port][1].inWaiting() == 0:
            pass
        msg = recieve_from_arduino(serial_ports, port)


def recieve_from_arduino(serial_ports, port):
    """Gets message from Arduino.

    Args:
      serial_ports: List containing address of USB ports, pySerial object, array number,
        and number of motors.
      port: Thread number created from enumerating through serial_ports.

    Returns:
      The string that was returned from the Arduino.
    """
    recieve_string = ""
    # any value that is not an end- or START_MARKER
    recieve_char = "z"
    recieve_char = serial_ports[port][1].read()
    recieve_char = recieve_char.decode("utf-8")
    # wait for the start character
    while ord(recieve_char) != START_MARKER:
        recieve_char = serial_ports[port][1].read()
        recieve_char = recieve_char.decode("utf-8")
    # save data until the end marker is found
    while ord(recieve_char) != END_MARKER:
        if ord(recieve_char) != START_MARKER:
            recieve_string = recieve_string + recieve_char
        recieve_char = serial_ports[port][1].read()
        recieve_char = recieve_char.decode("utf-8")
    return recieve_string


def move_arrays(serial_ports, parce_string, port):
    """Wait until the Arduino sends "Arduino Ready" - allows time for Arduino
    reset it also ensures that any bytes left over from a previous message are
    discarded.

    Args:
      serial_ports: List containing address of USB ports, pySerial object, array number,
        and number of motors.
      parce_string: String of commands sent to an array
      port: Thread number created from enumerating through serial_ports.
    """
    try:
        move_arrays_execute(serial_ports, parce_string, port)
    except timeout_decorator.TimeoutError:
        SPINNER.write(
            "== == Array: "
            + str(port)
            + " \033[31m"
            + "EXECUTION FAILED TIMEOUT"
            + "\033[0m"
        )


@timeout_decorator.timeout(100, use_signals=False)
def move_arrays_execute(serial_ports, parce_string, port):
    """Sends commands Arduino and then waits for a reply. Created off move_arrays() so
    we can have both a timeout and a try catch block.

    Args:
      serial_ports: List containing address of USB ports, pySerial object, array number,
        and number of motors.
      parce_string: String of commands sent to an array
      port: Thread number created from enumerating through serial_ports.
    """
    waiting_for_reply = False
    if not waiting_for_reply:
        serial_ports[port][1].write(parce_string.encode())
        SPINNER.write("-> -> Array: " + str(port) + " \033[32m" + "SENT" + "\033[0m")
        waiting_for_reply = True

    if waiting_for_reply:
        while serial_ports[port][1].inWaiting() == 0:
            pass
        data_recieved = recieve_from_arduino(serial_ports, port)
        SPINNER.write("<- <- Array: " + str(port) + " " + data_recieved)
        waiting_for_reply = False


def close_connections(serial_ports):
    """Closes serial port(s)

    Args:
      serial_ports: List containing address of USB ports, pySerial object, array number,
        and number of motors.
    """
    print("\nClosing Port(s)")
    SPINNER.start()
    for count, _ in enumerate(serial_ports):
        try:
            serial_ports[count][1] = serial_ports[count][1].close
            SPINNER.write(
                "Serial port "
                + str(count)
                + " "
                + serial_ports[count][0]
                + " \033[32m"
                + "CLOSED"
                + "\033[0m"
            )
        except AttributeError:
            SPINNER.write(
                "Serial port "
                + str(count)
                + " "
                + serial_ports[count][0]
                + " \033[31m"
                + "FAILED"
                + "\033[0m"
            )
            SPINNER.stop()
    SPINNER.stop()


def main():
    """Loop of the program. Provides tui to interact with the ceiling sculpture
    """
    # address of USB port,pySerial object, array number, and number of motors
    serial_ports = [USB_PATH]
    while True:
        try:
            # wait for user to want to run program
            input_text_1 = input(
                "\n\nPress Enter to Start the Program or type 'Exit' to Close:"
            )
            if input_text_1 in ("Exit", "exit"):
                break
            # initialize serial_objecs size based on the number of Arduinos
            # open ports at address /dev/ttyU* that we found earlier
            serial_ports = open_ports(serial_ports)
            # connect to the arrays and then save the array number and number of motors
            serial_ports = connect_to_arrays(serial_ports)
            # if error didn't occour exit this loop and move on to the next one
            break
        except Error:
            # if we got to connecting to ports then close ports otherwise loop
            if len(serial_ports) != 0:
                close_connections(serial_ports)
    while input_text_1 not in ("Exit", "exit"):
        try:
            print("===========\n")
            input_text_2 = input(
                "Enter the number of time you want the LED to blink or enter \
                'Exit' to close the program:\n : "
            )
            if input_text_2.isnumeric():
                execute_commands(serial_ports, "<" + input_text_2 + ">")
            elif input_text_2 in ("Exit", "exit"):
                close_connections(serial_ports)
                break
            else:
                print("Invalid Input\n")
        except Error:
            pass


# global variables
# don't change
BAUD_RATE = 9600
START_MARKER = 60
END_MARKER = 62
SPINNER = yaspin(Spinners.weather)
# adjustable
USB_PATH = "/dev/ttyUSB0"


if __name__ == "__main__":
    main()
