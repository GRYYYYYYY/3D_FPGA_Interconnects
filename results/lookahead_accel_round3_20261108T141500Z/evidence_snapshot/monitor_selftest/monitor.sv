module monitor; integer la_fd,la_both=7;initial begin la_fd=$fopen("test.json","w");
$fdisplay(la_fd,"{\"overlap_cycles\":%0d,\"engines\":[",la_both);
$fdisplay(la_fd,"{\"id\":0}]}");$fclose(la_fd);$finish;end endmodule
