import React from "react";
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from "@/components/ui/card";
import { Button } from "@/components/ui/button";

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
}

export abstract class BaseCard<T extends { id: string }> extends React.Component<BaseCardProps<T>> {
  config: CardConfig = {
    showEdit: true,
    showDelete: true,
    showFooter: true,
  };

  abstract renderHeader(): React.ReactNode;
  abstract renderContent(): React.ReactNode;
  abstract renderFooter(): React.ReactNode;

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
    if (this.props.onDelete) {
      this.props.onDelete(this.props.data.id);
    }
  };

  render() {
    return (
      <Card className="cursor-pointer hover:shadow-lg transition-shadow flex flex-col h-full" onClick={this.handleClick}>
        <CardHeader>{this.renderHeader()}</CardHeader>
        <CardContent className="flex-1">{this.renderContent()}</CardContent>
        {this.config.showFooter && (
          <CardFooter className="flex gap-2">
            {this.renderFooter()}
            {this.config.showEdit && (
              <Button variant="outline" size="sm" onClick={this.handleEdit}>
                Edit
              </Button>
            )}
            {this.config.showDelete && (
              <Button variant="destructive" size="sm" onClick={this.handleDelete}>
                Delete
              </Button>
            )}
          </CardFooter>
        )}
      </Card>
    );
  }
}
