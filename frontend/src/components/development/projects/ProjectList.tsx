import React from "react";
import { BaseCardList, BaseCardListProps } from "../../common/CardList/BaseCardList";
import { ProjectCard } from "./ProjectCard";
import { Project } from "@/types/project";

interface ProjectListProps extends BaseCardListProps<Project> {
  onDelete?: (id: string) => void;
  onEdit?: (id: string) => void;
  onClick?: (id: string) => void;
}

export class ProjectList extends BaseCardList<Project> {
  declare props: ProjectListProps;

  renderCard(project: Project) {
    return <ProjectCard data={project} onDelete={this.props.onDelete} onEdit={this.props.onEdit} onClick={this.props.onClick} />;
  }

  getEmptyMessage() {
    return "Aucun projet. Créez votre premier projet pour commencer.";
  }

  getSyncButtonLabel() {
    return "Rafraîchir";
  }

  getCreateButtonLabel() {
    return "Nouveau projet";
  }
}
