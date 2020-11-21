from gi.repository import GObject
from typing import List
import shutil
import logging
from gcompose.models.projects import Project
from gcompose.models.images import Image


class ImagesState(GObject.GObject):
    app = None

    images: List[Image] = GObject.Property(type=object)

    def __init__(self, app):
        super().__init__()
        self.app = app
        self.images = []

    def for_project(self, project_name: str) -> List[Image]:
        return [image for image in self.images if image.name == project_name]

    @GObject.Signal(arg_types=(object, object,))
    def update_project_images(self, project: Project, images: List[Image]):
        self.images = [
            image for image in self.images if image.project_name != project.name
        ] + images

    @GObject.Signal(arg_types=(object,))
    def request_images_for_project(self, project: Project):
        logging.debug("Dispatch images update")

        def on_result(result):
            logging.debug("Images cmd result")
            images_lines = result.splitlines()[2:]
            project_image_list = []
            for image_row in images_lines:
                container, repo, tag, image_id, size = [
                    val.strip() for val in image_row.split('   ') if val.strip()
                ]
                project_image_list.append(Image(
                    project_name=project.name,
                    container=container,
                    repository=repo,
                    tag=tag,
                    image_id=image_id,
                    size=size,
                ))
            self.emit("update_project_images", project, project_image_list)

        docker_compose_path = shutil.which('docker-compose')
        logging.debug(f'Docker-compose path: {docker_compose_path}')
        if not docker_compose_path:
            docker_compose_path = '/usr/local/bin/docker-compose'
            logging.debug(f'Docker-compose path to: {docker_compose_path}')

        self.app.spawn(
            command=f"{docker_compose_path} -f {str(project.path)} images",
            working_dir=project.path.parent,
            stdout_cb=on_result,
            use_sudo=project.use_sudo,
        )
