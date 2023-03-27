from tkinter import *
from tkinter import filedialog
from PIL import Image, ImageTk
import os


# Load images from a directory
def load_images(path):
    images = []
    for f in os.listdir(path):
        if f.lower().endswith((".png", ".jpg", ".jpeg", ".gif", ".bmp")):
            try:
                image = Image.open(os.path.join(path, f))
                images.append((f, image))
            except Exception as e:
                print(f"Error loading {f}: {e}")
    return images


# Create columns of image frames from a list of image directories
def create_image_columns(canvas, image_dirs, max_width=200, padding=10):
    columns = []
    for path in image_dirs:
        images = load_images(path)
        column_frames = []
        for img_name, img in images:
            img.thumbnail((max_width, max_width), Image.ANTIALIAS)
            photo = ImageTk.PhotoImage(img)
            frame = Frame(canvas, bd=2, relief="ridge")
            img_label = Label(frame, image=photo)
            img_label.image = photo
            img_label.pack()
            column_frames.append((img_name, frame))
        columns.append(column_frames)
    return columns


# Handle the start of a drag-and-drop operation
def on_drag_start(event):
    widget = event.widget
    widget.drag_data = {"frame": widget, "x": event.x, "y": event.y}


# Handle the dragging of an image frame
def on_drag(event):
    widget = event.widget
    x, y = widget.drag_data["x"], widget.drag_data["y"]
    dx = event.x - x
    dy = event.y - y
    widget.place(x=widget.winfo_x() + dx, y=widget.winfo_y() + dy)


# Get the bottom position of the last image in a column
def get_bottom_position(column_frames):
    max_y = 0
    for _, frame in column_frames:
        y = frame.winfo_y()
        if y > max_y:
            max_y = y
    return max_y + 210


# Handle the release of an image frame during drag-and-drop
def on_drag_release(event, columns):
    widget = event.widget
    target_column_index = widget.winfo_x() // 210
    if 0 <= target_column_index < len(columns):
        source_column = None
        source_index = None
        for column in columns:
            for idx, (img_name, frame) in enumerate(column):
                if frame == widget:
                    source_column = column
                    source_index = idx
                    break
            if source_column:
                break
        if source_column is not None:
            source_column.remove((img_name, widget))
            
            # Move up images in the source column to close the gap
            for idx, (_, frame) in enumerate(source_column[source_index:], start=source_index):
                frame.place(y=210 * idx + idx * 10)
                
        target_column = columns[target_column_index]
        insert_position = None
        if not target_column: # empty column
            insert_position = 0
            target_y = 0
        else:
            for idx, (_, frame) in enumerate(target_column):
                if widget.winfo_y() < frame.winfo_y():
                    insert_position = idx
                    break
            if insert_position is None:
                target_y = get_bottom_position(target_column)
                insert_position = len(target_column)
            else:
                target_y = 210 * insert_position + insert_position * 10
        
        widget.place_forget()
        widget.place(x=210 * target_column_index, y=target_y)
        target_column.insert(insert_position if insert_position is not None else len(target_column), (img_name, widget))
        
        # Re-adjust the positions of the images below the inserted image in the target column
        for idx, (_, frame) in enumerate(target_column[insert_position + 1:], start=insert_position + 1):
            frame.place(y=210 * idx + idx * 10)

# Bind drag-and-drop events to an image frame
def bind_drag_and_drop(widget, canvas, columns):
    widget.canvas = canvas
    widget.drag_data = {}
    widget.bind("<ButtonPress-1>", on_drag_start)
    widget.bind("<B1-Motion>", on_drag)
    widget.bind("<ButtonRelease-1>", lambda event: on_drag_release(event, columns))


# Delete an image frame from the canvas TODO make this move the images and fix bug
def delete_image(image_frame):
    image_frame.destroy()


# Enlarge an image in a separate window
def enlarge_image(image_path):
    enlarged_img = Image.open(image_path)
    photo = ImageTk.PhotoImage(enlarged_img)
    top = Toplevel()
    top.title("Enlarged Image")
    img_label = Label(top, image=photo)
    img_label.image = photo
    img_label.pack()


# Main function to


def main():
    image_dirs = [
        "images/1",
        "images/2",
        "images/3",
    ]

    # Create the main window and set its title and size
    root = Tk()
    root.title("Image Organizer")
    root.geometry("800x600")

    # Create a canvas and scrollbar for smooth scrolling through the images
    canvas = Canvas(root, bg="white")
    columns = create_image_columns(canvas, image_dirs)
    canvas.pack(side="left", fill="both", expand=True)
    scrollbar = Scrollbar(root, orient="vertical", command=canvas.yview)
    canvas.configure(yscrollcommand=scrollbar.set)
    scrollbar.pack(side="right", fill="y")

    # Draw black lines separating the columns
    for i in range(1, len(columns)):
        canvas.create_line(i * 210, 0, i * 210, 10000, fill="black", width=2)

    # Place the image frames in the canvas and add drag-and-drop and delete/enlarge functionality
    for i, column in enumerate(columns):
        for j, (img_name, frame) in enumerate(column):
            bind_drag_and_drop(frame, canvas, columns)
            delete_button = Button(
                frame, text="X", command=lambda f=frame: delete_image(f)
            )
            delete_button.pack(side="top", anchor="e")
            enlarge_button = Button(
                frame,
                text="Enlarge",
                command=lambda path=os.path.join(
                    image_dirs[i], img_name
                ): enlarge_image(path),
            )
            enlarge_button.pack(side="top", anchor="w")
            canvas.create_window(i * 210, j * 210 + j * 10, window=frame, anchor="nw")

    # Resize the canvas when the main window is resized
    def on_resize(event):
        canvas.configure(width=event.width, height=event.height)

    root.bind("<Configure>", on_resize)

    # Start the main event loop
    root.mainloop()


if __name__ == "__main__":
    main()
