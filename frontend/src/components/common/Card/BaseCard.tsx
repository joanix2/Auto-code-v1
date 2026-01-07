import React from "react";
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Edit, Trash2 } from "lucide-react";
import { DeleteDialog } from "@/components/DeleteDialog";

export interface BaseCardProps<T> {
  data: T;
  onDelete?: (id: string) => void;
  onEdit?: (id: string) => void;
  onClick?: (id: string) => void;
}

export interface CardConfig {
  showEdit?: boolean;
  showDelete?: boolean;
  showFooter?: boolean;
  deleteEntityName?: string; // Nom de l'entité pour le dialog de suppression
}

export abstract class BaseCard<T extends { id: string }> extends React.Component<BaseCardProps<T>> {
  state = {
    showDeleteDialog: false,
  };

  config: CardConfig = {
    showEdit: true,
    showDelete: true,
    showFooter: true,
    deleteEntityName: "élément", // Nom par défaut
  };

  abstract renderHeader(): React.ReactNode;
  abstract renderContent(): React.ReactNode;
  abstract renderFooter(): React.ReactNode;

  // Méthode abstraite pour obtenir le nom de l'entité à afficher dans la popup
  abstract getEntityDisplayName(): string;

  // Méthode pour personnaliser le titre de la popup de suppression
  getDeleteDialogTitle(): string {
    return `Supprimer ${this.config.deleteEntityName || "l'élément"}`;
  }

  // Méthode pour personnaliser la description de la popup de suppression
  getDeleteDialogDescription(): string {
    return `Êtes-vous sûr de vouloir supprimer ${this.getEntityDisplayName()} ? Cette action est irréversible.`;
  }

  handleClick = () => {
    if (this.props.onClick) {
      this.props.onClick(this.props.data.id);
    }
  };

  handleEdit = (e: React.MouseEvent) => {
    e.stopPropagation();
    if (this.props.onEdit) {
      this.props.onEdit(this.props.data.id);
    }
  };

  handleDelete = (e: React.MouseEvent) => {
    e.stopPropagation();
    this.setState({ showDeleteDialog: true });
  };

  handleConfirmDelete = () => {
    this.setState({ showDeleteDialog: false });
    if (this.props.onDelete) {
      // Use setTimeout to ensure dialog closes before triggering action
      setTimeout(() => {
        this.props.onDelete!(this.props.data.id);
      }, 0);
    }
  };

  render() {
    return (
      <>
        <Card className="cursor-pointer hover:shadow-lg transition-shadow flex flex-col h-full" onClick={this.handleClick}>
          <CardHeader>
            <div className="flex items-start gap-2">
              <div className="flex-1">{this.renderHeader()}</div>
              {(this.config.showEdit || this.config.showDelete) && (
                <div className="flex gap-1">
                  {this.config.showEdit && this.props.onEdit && (
                    <Button variant="ghost" size="sm" onClick={this.handleEdit} className="h-8 w-8 p-0">
                      <Edit className="h-4 w-4" />
                    </Button>
                  )}
                  {this.config.showDelete && this.props.onDelete && (
                    <Button variant="ghost" size="sm" onClick={this.handleDelete} className="h-8 w-8 p-0 text-red-600 hover:text-red-700 hover:bg-red-50">
                      <Trash2 className="h-4 w-4" />
                    </Button>
                  )}
                </div>
              )}
            </div>
          </CardHeader>
          <CardContent className="flex-1">{this.renderContent()}</CardContent>
          {this.config.showFooter && <CardFooter className="flex gap-2">{this.renderFooter()}</CardFooter>}
        </Card>

        <DeleteDialog
          open={this.state.showDeleteDialog}
          onOpenChange={(open) => this.setState({ showDeleteDialog: open })}
          title={this.getDeleteDialogTitle()}
          description={this.getDeleteDialogDescription()}
          variant="error"
          icon={Trash2}
          closeLabel="Annuler"
          confirmLabel="Supprimer"
          onConfirm={this.handleConfirmDelete}
        />
      </>
    );
  }
}
